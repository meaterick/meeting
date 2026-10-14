# 모임 장소 확인기

참여자의 출발지와 이동 방식, 비교할 장소를 입력하면 카카오 경로 API의 예상 시간·비용·거리를 표와 지도로 확인합니다.

## Streamlit Community Cloud 배포

1. 이 저장소의 `main` 브랜치와 `meeting_place.py`를 앱 파일로 선택합니다.
2. **Advanced settings → Secrets**에 다음 값을 입력합니다. 실제 키는 GitHub 파일에 넣지 않습니다.

```toml
KAKAO_REST_API_KEY = "본인의_카카오_REST_API_키"
```

3. 카카오 개발자 콘솔에서 해당 앱의 카카오맵 API 사용 상태와 REST API 키 설정을 확인합니다.

로컬에서 실행할 때는 `.streamlit/secrets.toml`에 같은 값을 저장하고 `python -m streamlit run meeting_place.py`를 실행합니다. `secrets.toml`은 저장소에 올리지 마세요.

이 프로그램은 사용자가 입력한 후보 장소만 비교하며, 자동차 연료비는 연비 12km/L와 유가 1,900원/L로 추정합니다.
