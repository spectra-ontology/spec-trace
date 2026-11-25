#!/usr/bin/env python3
"""native_word_conversion.py — validate Word conversions and recover tracked changes.

Spec: retained native Word source → well-formed derived OOXML and source receipt.
Ontology: accepted document text is the input to source-bound evidence locators.
Cycle: reject malformed direct export; render accepted native text in an isolated
LibreOffice process, export, reopen, and compare text before publishing a result.
사용: /usr/bin/python3 -B native_word_conversion.py --source FILE --output FILE --receipt FILE
LLM 호출: 없음. Source files are read and never saved by this utility.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import tempfile
import threading
import time
import unicodedata
import uuid
import xml.etree.ElementTree as ET
import zipfile


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def _identity(path):
    value = Path(path).stat()
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def validate_docx(path):
    """Validate CRC and XML syntax, including the full main document part."""
    with zipfile.ZipFile(path) as archive:
        if 'word/document.xml' not in archive.namelist() or archive.testzip() is not None:
            raise ValueError('DOCX requires an intact main document part')
        for name in archive.namelist():
            if name.endswith(('.xml', '.rels')):
                ET.fromstring(archive.read(name))


def normalized_rendered_text(text):
    """Ignore layout whitespace only; preserve punctuation, values and operators."""
    return re.sub(r'\s+', '', unicodedata.normalize('NFC', text))


def require_same_rendered_text(before, after):
    left, right = map(normalized_rendered_text, (before, after))
    if left != right:
        raise ValueError('Accepted native text changed on DOCX reopen')
    return {'normalization': 'Unicode NFC; remove layout whitespace only',
            'nativeCharacters': len(before), 'reopenedCharacters': len(after),
            'normalizedCharacters': len(left),
            'normalizedTextSha256': hashlib.sha256(left.encode()).hexdigest(),
            'equal': True}


def _signal_process(process, signum, *, process_group):
    """Signal this owned child, or the separate group created for this child."""
    try:
        if process_group:
            if process.pid <= 1 or process.pid == os.getpgrp():
                raise ValueError('Refusing to signal the caller process group')
            try:
                actual_group = os.getpgid(process.pid)
            except ProcessLookupError:
                # The leader may have exited while its descendants still run.
                pass
            else:
                if actual_group != process.pid:
                    raise ValueError('Child does not own a separate process group')
            os.killpg(process.pid, signum)
        else:
            process.send_signal(signum)
    except ProcessLookupError:
        pass


def _stop(process, *, process_group=True):
    """Wait for a standalone converter; signal only its owned PID or group."""
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _signal_process(process, signal.SIGTERM, process_group=process_group)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _signal_process(process, signal.SIGKILL, process_group=process_group)
            process.wait(timeout=5)


def _stop_owned_group(process, *, timeout=5):
    """Stop a supervised session, including descendants after its leader exits."""
    try:
        try:
            _signal_process(process, signal.SIGTERM, process_group=True)
        finally:
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                pass
    finally:
        # A terminated leader does not prove that a TERM-resistant child exited.
        try:
            _signal_process(process, signal.SIGKILL, process_group=True)
        finally:
            try:
                process.wait(timeout=timeout)
            finally:
                for stream in (process.stdout, process.stderr):
                    if stream is not None:
                        stream.close()


@contextmanager
def _supervised_termination():
    """Let main-thread SIGTERM unwind the same cleanup path as interruption."""
    main_thread = threading.current_thread() is threading.main_thread()
    previous = signal.getsignal(signal.SIGTERM) if main_thread else None

    def terminated(signum, frame):
        raise SystemExit(128 + signum)

    if main_thread:
        signal.signal(signal.SIGTERM, terminated)
    try:
        yield
    finally:
        if main_thread:
            signal.signal(signal.SIGTERM, previous)


def recover_native_word(source, output, *, soffice='soffice', supervised_process_group=False):
    """Export an accepted view, preserving source bytes and an exclusive output.

    Requires system Python's pyuno. Change acceptance occurs in memory; the
    original native file is never a save destination. The actual reopened text
    must equal the accepted native rendering, including tables. A supervised CLI
    keeps LibreOffice in its supervisor-owned group; independent calls retain a
    separate converter session.
    """
    if supervised_process_group and os.getpid() != os.getpgrp():
        raise ValueError('Supervised recovery requires its own process-group leader')
    import uno
    from com.sun.star.beans import PropertyValue

    source, output = Path(source).resolve(strict=True), Path(output).absolute()
    if output.exists() or source == output:
        raise FileExistsError('Recovery requires a new output path')
    before_sha = sha256(source)
    before_stat = _identity(source)
    output.parent.mkdir(parents=True, exist_ok=True)

    def properties(**values):
        result = []
        for name, value in values.items():
            item = PropertyValue()
            item.Name, item.Value = name, value
            result.append(item)
        return tuple(result)

    with tempfile.TemporaryDirectory(prefix='.native-word-', dir=output.parent) as tmp:
        directory = Path(tmp)
        pipe = 'spectra_' + uuid.uuid4().hex
        process = subprocess.Popen([soffice, '--headless',
            '-env:UserInstallation=' + (directory/'profile').as_uri(),
            '--accept=pipe,name=' + pipe + ';urp;StarOffice.ComponentContext',
            '--norestore', '--nodefault', '--nofirststartwizard'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=not supervised_process_group)
        desktop, document, reopened = None, None, None
        try:
            local = uno.getComponentContext()
            resolver = local.ServiceManager.createInstanceWithContext(
                'com.sun.star.bridge.UnoUrlResolver', local)
            for _ in range(100):
                try:
                    context = resolver.resolve('uno:pipe,name=' + pipe + ';urp;StarOffice.ComponentContext')
                    break
                except Exception:
                    if process.poll() is not None:
                        raise RuntimeError('Isolated LibreOffice exited during startup')
                    time.sleep(0.1)
            else:
                raise TimeoutError('Isolated LibreOffice startup timed out')
            manager = context.ServiceManager
            desktop = manager.createInstanceWithContext('com.sun.star.frame.Desktop', context)
            load = dict(Hidden=True, UpdateDocMode=uno.getConstantByName(
                'com.sun.star.document.UpdateDocMode.NO_UPDATE'),
                MacroExecutionMode=uno.getConstantByName(
                'com.sun.star.document.MacroExecMode.NEVER_EXECUTE'))
            document = desktop.loadComponentFromURL(source.as_uri(), '_blank', 0,
                properties(**load, ReadOnly=False))
            if document is None:
                raise ValueError('Native Word source could not be opened')
            redlines_before = document.Redlines.Count
            document.RecordChanges = False
            dispatcher = manager.createInstanceWithContext('com.sun.star.frame.DispatchHelper', context)
            dispatcher.executeDispatch(document.CurrentController.Frame,
                '.uno:AcceptAllTrackedChanges', '', 0, ())
            if document.Redlines.Count:
                raise ValueError('Native accepted view retains unresolved redlines')
            baseline = document.Text.String
            candidate = directory/'accepted.docx'
            document.storeToURL(candidate.as_uri(), properties(FilterName='Office Open XML Text', Overwrite=False))
            document.close(True)
            document = None
            validate_docx(candidate)
            reopened = desktop.loadComponentFromURL(candidate.as_uri(), '_blank', 0,
                properties(**load, ReadOnly=True))
            if reopened is None or reopened.Redlines.Count:
                raise ValueError('Reopened accepted DOCX has unresolved redlines')
            comparison = require_same_rendered_text(baseline, reopened.Text.String)
            reopened.close(True)
            reopened = None
            if _identity(source) != before_stat or sha256(source) != before_sha:
                raise ValueError('Native source changed during conversion')
            candidate_sha = sha256(candidate)
            with candidate.open('rb') as stream:
                os.fsync(stream.fileno())
            # Exclusive publication also protects against another writer creating output.
            os.link(candidate, output)
            return {'schema': 1, 'status': 'verified', 'method': 'native_accepted_uno_export_reopen',
                'source': str(source), 'sourceSha256': before_sha,
                'output': str(output), 'outputSha256': candidate_sha,
                'strictXml': True, 'redlinesBefore': redlines_before, 'redlinesAfter': 0,
                'acceptedRenderedText': comparison,
                'converterVersion': subprocess.run([soffice, '--version'], capture_output=True,
                    text=True, timeout=10, check=True).stdout.strip()}
        finally:
            try:
                for component in (reopened, document):
                    if component is not None:
                        component.close(True)
                if desktop is not None:
                    desktop.terminate()
            finally:
                _stop(process, process_group=not supervised_process_group)


def ensure_valid_conversion(produced, source, *, soffice='soffice', timeout=600):
    """Validate a fresh direct export; recover it before a producer publishes it."""
    try:
        validate_docx(produced)
        return None
    except (ValueError, zipfile.BadZipFile, ET.ParseError):
        pass
    produced = Path(produced)
    source_sha = sha256(source)
    with _supervised_termination(), tempfile.TemporaryDirectory(prefix='.checked-word-', dir=produced.parent) as tmp:
        directory = Path(tmp)
        output, receipt = directory/'accepted.docx', directory/'receipt.json'
        command = ['/usr/bin/python3', '-B', str(Path(__file__).resolve()),
            '--source', str(Path(source).resolve()), '--output', str(output),
            '--receipt', str(receipt), '--soffice', soffice, '--supervised-process-group']
        process = None
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, start_new_session=True)
            _, error = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            raise TimeoutError('Accepted native conversion timed out')
        finally:
            if process is not None:
                _stop_owned_group(process)
        if process.returncode:
            raise ValueError('Accepted native conversion failed: ' + error[-1000:])
        result = json.loads(receipt.read_text())
        validate_docx(output)
        if (result.get('status') != 'verified'
                or result.get('sourceSha256') != source_sha or sha256(source) != source_sha
                or result.get('strictXml') is not True or result.get('redlinesAfter') != 0
                or result.get('acceptedRenderedText', {}).get('equal') is not True
                or sha256(output) != result.get('outputSha256')):
            raise ValueError('Accepted conversion receipt differs from output')
        os.replace(output, produced)
        return result


def publish_validated_conversion(produced, output, source, *, soffice='soffice', timeout=600):
    """Publish a fresh converter output only after XML/accepted-view validation."""
    result = ensure_valid_conversion(produced, source, soffice=soffice, timeout=timeout)
    shutil.move(str(produced), str(output))
    if result is not None:
        result['output'] = str(Path(output).resolve())
        if sha256(output) != result['outputSha256']:
            raise ValueError('Published accepted conversion differs from its receipt')
        receipt = Path(str(output) + '.conversion.json')
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=receipt.parent,
                                        prefix='.' + receipt.name, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.replace(temporary, receipt)
        finally:
            temporary.unlink(missing_ok=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--soffice', default='soffice')
    parser.add_argument('--supervised-process-group', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    result = recover_native_word(args.source, args.output, soffice=args.soffice,
                                 supervised_process_group=args.supervised_process_group)
    args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'outputSha256': result['outputSha256']}))


if __name__ == '__main__':
    main()
