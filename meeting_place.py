import json
import streamlit as st
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    KAKAO_REST_API_KEY = st.secrets["KAKAO_REST_API_KEY"]
except (KeyError, FileNotFoundError):
    st.error("앱 설정의 Secrets에 KAKAO_REST_API_KEY를 등록해 주세요.")
    st.stop()


def kakao(base, path, params):
    url = f"{base}{path}?{urlencode(params)}"
    request = Request(url, headers={"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"})
    try:
        with urlopen(request, timeout=12) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise ValueError(f"API 조회 실패: {error}") from error


def search_location(query):
    for path, name_field in (
        ("/v2/local/search/address.json", "address_name"),
        ("/v2/local/search/keyword.json", "place_name"),
    ):
        data = kakao("https://dapi.kakao.com", path, {"query": query})
        if data.get("documents"):
            item = data["documents"][0]
            return {"name": item[name_field], "x": float(item["x"]), "y": float(item["y"])}
    raise ValueError(f"장소를 찾을 수 없습니다: {query}")


def route(person, place):
    if person["mode"] == "대중교통":
        data = kakao("https://dapi.kakao.com", "/v2/routing/publictraffic", {
            "start_x": person["x"], "start_y": person["y"],
            "end_x": place["x"], "end_y": place["y"],
        })
        if data.get("status") != "OK" or not data.get("routes"):
            raise LookupError("대중교통 경로가 없습니다.")
        best = min((item["properties"] for item in data["routes"]),
                   key=lambda item: item["totalTime"])
        fare = best.get("fare", {})
        return (round(best["totalTime"] / 60, 1),
                int(fare.get("value") or fare.get("min") or 0),
                round(best["totalDistance"] / 1000, 2))
    elif person["mode"] == "자동차":
        data = kakao("https://apis-navi.kakaomobility.com", "/v1/directions", {
            "origin": f"{person['x']},{person['y']}",
            "destination": f"{place['x']},{place['y']}",
            "priority": "RECOMMEND", "summary": "true",
        })
        routes = data.get("routes", [])
        if not routes or routes[0].get("result_code") != 0:
            raise LookupError("자동차 경로가 없습니다.")
        summary = routes[0]["summary"]
        distance = summary["distance"] / 1000
        cost = int(summary.get("fare", {}).get("toll", 0)) + round(distance / 12 * 1900)
        return (round(summary["duration"] / 60, 1), cost, round(distance, 2))
    else:
        raise ValueError("지원하지 않는 이동 방식입니다.")


def compare(people, places):
    results = []
    for place in places:
        try:
            trips = [route(person, place) for person in people]
        except LookupError:
            continue
        results.append({
            "장소": place["name"],
            "최장 시간(분)": max(trip[0] for trip in trips),
            "총비용(원)": sum(trip[1] for trip in trips),
            "총거리(km)": round(sum(trip[2] for trip in trips), 2),
        })
    results.sort(key=lambda row: (
        row["최장 시간(분)"], row["총비용(원)"], row["총거리(km)"],
    ))
    return results


def run():

    st.title("모임 장소 확인기")
    st.subheader("참여자 출발지")
    count = st.number_input("참여자 수", min_value=2, max_value=5, value=2)
    header = st.columns([1, 3, 1])
    for column, label in zip(header, ("이름", "출발지 주소/역명", "이동 방식")):
        column.markdown(f"**{label}**")
    inputs = []
    for index in range(count):
        columns = st.columns([1, 3, 1])
        name = columns[0].text_input(f"이름 {index + 1}", value=f"참여자{index + 1}",
                                     label_visibility="collapsed")
        origin = columns[1].text_input(f"출발지 {index + 1}", label_visibility="collapsed")
        mode = columns[2].selectbox(f"이동 방식 {index + 1}", ["대중교통", "자동차"],
                                    label_visibility="collapsed")
        inputs.append((name, origin, mode))

    st.subheader("비교할 장소")
    count_places = st.number_input("장소 수", min_value=2, max_value=5, value=2)
    columns = st.columns(2)
    place_names = [columns[i % 2].text_input(f"장소 {i + 1} 주소/이름")
                   for i in range(count_places)]
    if not st.button("경로 비교하기"):
        return
    if any(not origin.strip() for _, origin, _ in inputs) or any(
        not name.strip() for name in place_names
    ):
        st.error("출발지와 비교할 장소를 모두 입력하세요.")
        return

    try:
        people = []
        for name, origin, mode in inputs:
            people.append({"person": name, "mode": mode, **search_location(origin)})
        places = [search_location(name) for name in place_names]
        results = compare(people, places)
    except ValueError as error:
        st.error(str(error))
        return
    if not results:
        st.error("조회 가능한 경로가 없습니다.")
        return

    points = ([{"lat": p["y"], "lon": p["x"], "color": "#2563eb"} for p in people]
              + [{"lat": p["y"], "lon": p["x"], "color": "#ea580c"} for p in places])
    st.map(points, latitude="lat", longitude="lon", color="color")
    st.dataframe([{"이름": p["person"], "검색된 출발지": p["name"],
                   "이동 방식": p["mode"]} for p in people], hide_index=True)
    st.dataframe([{"순위": rank, **result} for rank, result in enumerate(results, 1)],
                 hide_index=True)
    st.caption("자동차 비용은 통행료와 추정 연료비(연비 12km/L, 유가 1,900원/L)의 합입니다.")


if __name__ == "__main__":
    run()
