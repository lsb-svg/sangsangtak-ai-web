# 상상탁구 AI — 구글 검색 홍보 웹사이트 (실제 재구축본)

이 프로젝트는 **새로 작성한 최소 실행본**입니다. 이전 Gemini 보고서의 파일·로그·해시는 실물로 확인되지 않았으며, 그 결과물을 복원한 것으로 주장하지 않습니다.

## 실행

Python 3.11 이상에서, 프로젝트 폴더에서:

```powershell
python build.py
python verify.py
python -m http.server 8080 -d dist
```

브라우저에서 `http://localhost:8080` 접속. GitHub Pages에 공개하려면 이 프로젝트의 파일을 `lsb-svg/sangsangtak-ai-web` 저장소에 업로드하고 Settings → Pages → Source = GitHub Actions 를 설정합니다. **현재 ZIP은 GitHub에 업로드되지 않았습니다.**

## 포함된 것

- 홈 + 실용 정보 3편, Python 표준 라이브러리 빌드, 사이트맵, 로봇 지침
- 원본 QR 2개 그대로 사용 (Android/iOS). QR 내부 URL은 로컬에서 해독해 확인
- 각각의 공식 스토어 다운로드 링크
- GitHub Actions 배포 워크플로
- `verify.py`로 상대 경로 및 HTML 내 스토어 링크 검사

## 포함되지 않은 것

- 다른 작업창의 홍보 포스터 **개별 원본 4장**: 이번 채팅에는 축소된 모음 스크린샷만 있으므로 임의로 잘라서 '원본'이라고 하지 않음
- 실시간 사실 검증, AI 신규 글 자동 작성, 방문자 집계, 다운로드 설치 추적
- 실제 GitHub Actions 실행, 실제 Pages 공개, 모바일 실기기 검증

## 홍보물 4종 원본 적용

4개 개별 원본 JPG/PNG가 확보되면 `static/posters/`에 넣고 웹페이지 배치 작업을 수행하세요. QR 이미지는 현재 `static/qr/`의 원본 PNG를 계속 사용하세요.

## 주의

이 문서는 의학·규칙 판정용 권위 자료가 아니라 일반적인 참고 안내입니다. 국내·국제 대회 규정에 대한 최신성 검사는 별도로 필요합니다.


## 질문·답변 검색 업그레이드 (2026-11-02)
- `questions/*.json`: 검토 가능한 질문/답변 데이터. `review_status`는 편집 검토 여부를 명시합니다. 검증을 자동 보증하지 않습니다.
- 첫 화면의 검색은 **사이트 내부 질문 제목 검색**입니다. Google 이용자 실시간 질문을 읽거나 Google 검색어를 자동 수집하지 않습니다.
- 각 답변은 독립 HTML URL 및 canonical/sitemap으로 연결됩니다. Google 색인/노출/순위는 보장되지 않습니다.
- 새 질문은 기존 JSON 형식으로 추가하고 **사람이 출처와 사실을 확인**한 뒤 발행하세요. 변경하면 GitHub Actions가 빌드 및 배포합니다.
- `python build.py` 다음 `python verify.py`를 실행하세요. 기존 Android/iPhone QR 원본을 유지합니다.
- Google Search Console 등록 및 질문 수요 조사는 별도 단계이며 자동 수집 구현은 포함되지 않습니다.
- 기존 4종 홍보 포스터 개별 원본은 제공받지 못해 이 버전에는 포함되지 않습니다.
