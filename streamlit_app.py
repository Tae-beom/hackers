import streamlit as st
import pandas as pd
import random
import re
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="해커스 보카 유의어 퀴즈", layout="centered")

# --- UI 스타일링 (CSS) ---
st.markdown("""
    <style>
    /* 🔥 화면 밀림 방지: 오른쪽 스크롤바 자리를 항상 고정시킵니다. */
    [data-testid="stAppViewContainer"] {
        overflow-y: scroll !important;
    }
    
    .block-container { max-width: 800px; min-height: 101vh; padding-top: 2rem; }
    .word-box {
        background-color: #A6C8E6; 
        color: black;
        padding: 30px;
        text-align: center;
        font-size: 40px;
        font-weight: bold;
        border-radius: 10px;
        margin-bottom: 30px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        width: 100%; 
    }
    div[data-testid="column"] { display: flex; justify-content: center; }
    div.stButton { width: 100%; display: flex; justify-content: center; }
    div.stButton > button {
        background-color: #FFF9A6 !important; 
        color: black !important;
        min-height: 70px !important; 
        height: auto !important; 
        width: 100% !important; 
        border: 1px solid #ccc !important;
        border-radius: 5px !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 10px !important;
    }
    div.stButton > button:hover {
        background-color: #F0E68C !important;
        border: 1px solid #999 !important;
    }
    div.stButton > button * {
        font-size: 22px !important; 
        white-space: normal !important; 
        word-wrap: break-word !important; 
        text-align: center !important; 
        line-height: 1.2 !important; 
    }
    .result-text {
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 📌 단어장 파일 목록 설정 ---
voca_files = {
    "Day 2 (해커스 보카)": "vocafile/Hackers_Voca_Day2_with_Synonyms.xlsx",
    "Day 2A (해커스 보카)": "vocafile/Hackers_Voca_Day2_1-23.xlsx",
    "Day 2B (해커스 보카)": "vocafile/Hackers_Voca_Day2_24-56.xlsx"
    # 나중에 추가할 파일명은 여기에 적어주세요.
}

# --- 단어 출제 기록 초기화 ---
if 'used_synonyms_history' not in st.session_state:
    st.session_state.used_synonyms_history = {}

# --- 상태 초기화 함수 ---
def init_game(df):
    st.session_state.score = 0
    st.session_state.total_played = 0
    st.session_state.remaining_words = df['단어'].tolist()
    st.session_state.total_questions = len(st.session_state.remaining_words)
    st.session_state.game_over = False
    generate_question(df)

# --- 문제 생성 함수 ---
def generate_question(df):
    if not st.session_state.remaining_words:
        st.session_state.game_over = True
        return
        
    word = random.choice(st.session_state.remaining_words)
    st.session_state.remaining_words.remove(word)
    
    correct_row = df[df['단어'] == word].iloc[0]
    all_synonyms = [s.strip() for s in re.split(r'[,;]', str(correct_row['동의어'])) if s.strip()]
    
    history = st.session_state.used_synonyms_history.get(word, [])
    unused_synonyms = [s for s in all_synonyms if s not in history]
    
    if not unused_synonyms:
        unused_synonyms = all_synonyms 
        st.session_state.used_synonyms_history[word] = [] 
        
    correct_synonym = random.choice(unused_synonyms)
    
    if word not in st.session_state.used_synonyms_history:
        st.session_state.used_synonyms_history[word] = []
    st.session_state.used_synonyms_history[word].append(correct_synonym)
    
    distractor_rows = df[df['단어'] != word].sample(n=2)
    distractors = []
    for _, row in distractor_rows.iterrows():
        d_synonyms = [s.strip() for s in re.split(r'[,;]', str(row['동의어'])) if s.strip()]
        distractors.append(random.choice(d_synonyms))
        
    options = [correct_synonym] + distractors
    random.shuffle(options)
    
    st.session_state.current_word = word
    st.session_state.correct_answer = correct_synonym
    st.session_state.options = options
    st.session_state.answered = False
    st.session_state.result_msg = ""

# --- 정답 확인 함수 ---
def check_answer(selected):
    st.session_state.answered = True
    st.session_state.total_played += 1
    if selected == st.session_state.correct_answer:
        st.session_state.score += 1
        st.session_state.result_msg = "<div class='result-text' style='color: green;'>정답입니다! 🎉</div>"
    else:
        st.session_state.result_msg = f"<div class='result-text' style='color: red;'>틀렸습니다! 정답은 '{st.session_state.correct_answer}' 입니다. 😢</div>"

# --- 메인 화면 로직 ---
st.title("📚 영단어 유의어 맞추기 게임")

# 단어장 선택 드롭다운
selected_voca = st.selectbox("👇 학습할 단어장을 선택하세요", list(voca_files.keys()))
file_path = voca_files[selected_voca]

# 단어장이 변경되면 게임 상태를 완전 초기화
if 'current_voca' not in st.session_state or st.session_state.current_voca != selected_voca:
    st.session_state.current_voca = selected_voca
    if 'remaining_words' in st.session_state:
        del st.session_state['remaining_words']
    st.session_state.used_synonyms_history = {}

# 파일이 존재하는지 확인 후 게임 실행
if os.path.exists(file_path):
    df = pd.read_excel(file_path)
    df = df.dropna(subset=['단어', '동의어'])
    
    if len(df) < 3:
        st.error("데이터가 부족합니다. 최소 3개 이상의 동의어 데이터가 필요합니다.")
        st.stop()
        
    if 'remaining_words' not in st.session_state:
        init_game(df)
        
    if getattr(st.session_state, 'game_over', False):
        st.markdown(f"""
            <div class='result-text' style='color: #2563eb; font-size: 36px; padding: 40px 0;'>
                🎊 {selected_voca} 세트 종료! 🎊<br>
                최종 점수: {st.session_state.score} / {st.session_state.total_questions}
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 다음 세트 다시하기", use_container_width=True):
            init_game(df)
            st.rerun()
            
    else:
        # 🔥 수정된 부분: 정확한 현재 문제 번호 계산 (전체 문제 - 남은 문제)
        current_q_num = st.session_state.total_questions - len(st.session_state.remaining_words)
        
        # 🔥 수정된 부분: 점수와 진행 번호를 직관적으로 표시
        st.subheader(f"🏆 정답: {st.session_state.score}개 (진행: {current_q_num} / {st.session_state.total_questions})")
        
        st.markdown(f"<div class='word-box'>{st.session_state.current_word}</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(st.session_state.options[0], disabled=st.session_state.answered, key="opt0", use_container_width=True):
                check_answer(st.session_state.options[0])
                st.rerun()
        with col2:
            if st.button(st.session_state.options[1], disabled=st.session_state.answered, key="opt1", use_container_width=True):
                check_answer(st.session_state.options[1])
                st.rerun()
        with col3:
            if st.button(st.session_state.options[2], disabled=st.session_state.answered, key="opt2", use_container_width=True):
                check_answer(st.session_state.options[2])
                st.rerun()
                
        if st.session_state.answered:
            st.markdown(st.session_state.result_msg, unsafe_allow_html=True)
            btn_text = "결과 확인" if len(st.session_state.remaining_words) == 0 else "➡️ 다음 단어"
            if st.button(btn_text, key="next_btn", use_container_width=True):
                generate_question(df)
                st.rerun()
else:
    st.error(f"⚠️ '{file_path}' 파일을 찾을 수 없습니다.")
    st.info("💡 해결 방법: 깃허브 저장소(Repository)에 app.py 파일과 같은 위치에 엑셀 파일을 업로드해주세요.")