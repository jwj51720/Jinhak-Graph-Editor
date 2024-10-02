import streamlit as st
from py2neo import Graph

# """
# # 사용 방법
# streamlit run st.py

# """


# Neo4j 연결 설정
import os

neo4j_url = os.getenv("NEO4J_URL")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")
neo4j_db_name = os.getenv("NEO4J_DB_NAME")

graph = Graph(neo4j_url, auth=(neo4j_user, neo4j_password), name=neo4j_db_name)


# 키워드로 CHUNK 노드 찾기 함수
def find_chunks_with_keywords(keywords):
    keyword_list = keywords.split()
    conditions = " AND ".join([f"n.text CONTAINS '{word}'" for word in keyword_list])

    query = f"""
    MATCH (n:CHUNK)
    WHERE {conditions}
    RETURN n.id AS id, n.text AS text
    """

    result = graph.run(query)
    result_list = []
    for record in result:
        result_list.append({"id": record["id"], "text": record["text"]})
    return result_list


# 텍스트 요약 함수 (처음과 끝 일부를 보여주기)
def summarize_text(text, max_length=100):
    if len(text) > max_length:
        return text[:50] + " ... " + text[-50:]
    return text


# 키워드 입력 시 session_state를 리셋하는 함수
def reset_session_state():
    if "selected_chunk_id" in st.session_state:
        del st.session_state["selected_chunk_id"]
    if "selected_chunk_text" in st.session_state:
        del st.session_state["selected_chunk_text"]


# Streamlit UI 구성
st.title("Neo4j CHUNK 수정 툴")
st.info(
    "💡Relation을 수정하는 것이 아니기 때문에 내용 삭제보다는 추가 및 수정을 권장합니다."
)

# 키워드 입력 받기
keyword = st.text_input("키워드를 입력하세요:", value="", on_change=reset_session_state)

# 키워드로 CHUNK 찾기
if keyword:
    chunks = find_chunks_with_keywords(keyword)

    # 결과 보여주기
    if chunks:
        st.write(f"'{keyword}'에 해당하는 CHUNK를 찾았습니다. CHUNK를 선택하세요:")

        # 바둑판식 UI로 표시 (4개의 컬럼으로 표시)
        num_columns = 4  # 한 줄에 4개의 버튼
        chunk_count = len(chunks)

        # 버튼을 바둑판 형태로 배치
        for i in range(0, chunk_count, num_columns):
            cols = st.columns(num_columns)  # 4개의 컬럼 생성
            for j, col in enumerate(cols):
                if i + j < chunk_count:
                    chunk = chunks[i + j]
                    # 텍스트 요약을 버튼에 표시
                    if col.button(
                        f"ID: {chunk['id']}\n{summarize_text(chunk['text'])}"
                    ):
                        # 선택한 CHUNK ID와 텍스트를 session_state에 저장
                        st.session_state["selected_chunk_id"] = chunk["id"]
                        st.session_state["selected_chunk_text"] = chunk["text"]

        # 선택된 CHUNK 보여주기 및 수정
        if "selected_chunk_id" in st.session_state:
            st.write(
                "선택한 CHUNK의 ID:", st.session_state["selected_chunk_id"]
            )  # 선택한 ID를 표시
            st.write("선택한 CHUNK의 내용:")
            new_text = st.text_area(
                "내용을 수정하세요:",
                value=st.session_state["selected_chunk_text"],
                height=600,
                key="chunk_text_area",
            )

            # 저장 버튼
            if st.button("수정 내용 저장"):
                chunk_id = st.session_state["selected_chunk_id"]
                query = f"""
                MATCH (n:CHUNK {{id: $chunk_id}})
                SET n.text = $new_text
                RETURN n
                """
                graph.run(
                    query, parameters={"chunk_id": chunk_id, "new_text": new_text}
                )
                st.success(f"CHUNK ID: {chunk_id}의 수정이 완료되었습니다.")
    else:
        st.write(f"'{keyword}'에 해당하는 CHUNK를 찾을 수 없습니다.")
