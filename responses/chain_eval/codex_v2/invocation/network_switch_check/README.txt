codex exec 의 workspace-write 샌드박스가 localhost TCP 를 막는지, 어느 설정으로 여는지 확인한 기록.
같은 명령(codex exec --json --skip-git-repo-check --ignore-user-config -s workspace-write -C <t.py 가 있는 폴더>)을
두 번 돌렸고, 두 번째에만 -c sandbox_workspace_write.network_access=true 를 더했다. 과제는 t.py 를 실행해 그 출력을
돌려주는 것이었다(프롬프트 원문은 남기지 않았다).
- ev_off.jsonl / err_off.txt: 설정 없음. socket() 이 PermissionError [Errno 1] Operation not permitted 로 실패.
- ev_on.jsonl / err_on.txt: 설정 켬. "tcp ok"(127.0.0.1:7687 에 TCP 연결만 열고 닫음), 홈 디렉토리 쓰기는 여전히 거부.
err_*.txt 의 rmcp 오류는 사용자 설정 밖에서 읽힌 MCP 서버의 인증 실패이며 두 실행에 똑같이 나온다.
