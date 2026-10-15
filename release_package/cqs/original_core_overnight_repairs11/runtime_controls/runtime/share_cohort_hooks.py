"""Value-free V8 share hooks for a fresh isolated cohort only."""
import importlib
import share_runtime_adapter as share


def install_runtime(runtime):
    if getattr(runtime, '_cohort_exact_share_hooks_installed', False):
        return
    structured = importlib.import_module('structured_adapter')
    retrieval = importlib.import_module('retrieval_adapter')
    share.install(structured, retrieval)
    old_public = runtime.public_task
    def public_task(task):
        return share.public_task(task, old_public)
    runtime.public_task = public_task
    runtime._cohort_exact_share_hooks_installed = True
