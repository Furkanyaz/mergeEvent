import streamlit as st
import random
import pandas as pd
import copy

st.set_page_config(page_title="Merge Event Simülasyonu", layout="wide")

MAX_LOOPS = 50000

st.title("🏆 Merge Event Simülasyonu")
st.markdown("""
Bu simülasyon, bir merge eventinde bir kullanıcının herhangi bir elemente ulaşmak için kaç bölüm oynaması gerektiğini tahmin eder.
""")

st.sidebar.header("⚙️ Simülasyon Parametreleri")
st.sidebar.markdown("Buradaki değerleri değiştirerek farklı senaryoları test edebilirsiniz.")
st.sidebar.subheader("Board Tasarımı")
st.sidebar.caption("Her kareyi 'Seviye-Durum' (örn: 5K, 1A, 3Y) formatında, virgülle ayırarak 8 satır ve 6 sütun olarak girin.")
default_board_layout = """0K,8K,7K,8K,7K,0K
7K,6K,0K,6K,8K,7K
7K,7K,5K,3K,7K,7K
7K,5K,7K,7K,1K,5K
2K,7K,0K,3K,7K,7K
0K,2K,1K,5K,2K,3K
1K,2Y,0A,2Y,1Y,1K
1Y,0A,0A,1A,0A,1Y
"""
board_text_input = st.sidebar.text_area("Başlangıç Board Düzeni:", default_board_layout, height=210)
max_element_level = st.sidebar.number_input("Element Sayısı", min_value=3, value=12, step=1)
start_level = st.sidebar.number_input("Başlangıç Seviyesi", min_value=1, value=1, step=1)
st.sidebar.markdown("---")
st.sidebar.subheader("L2 Üretim Olasılıkları")
initial_probs = {}
for i in range(5, max_element_level):
    default_prob = min(5 + (i - 5) * 5, 30)
    initial_probs[i] = st.sidebar.slider(f"Level {i}'e Ulaşılınca (%)", 0, 100, default_prob, 1, key=f"prob_{i}")
initial_probs_float = {level: prob / 100.0 for level, prob in initial_probs.items()}

def parse_board_from_text(text_layout):
    board = []
    try:
        lines = [line.strip() for line in text_layout.strip().split('\n') if line.strip()]
        for line in lines:
            row = []
            cells = [cell.strip() for cell in line.split(',')]
            for cell_str in cells:
                level = int(cell_str[:-1])
                state_char = cell_str[-1].upper()

                if state_char == 'A':
                    state = 'open'
                elif state_char == 'Y':
                    state = 'semi-open'
                else:
                    state = 'closed'

                row.append({'level': level, 'state': state})
            board.append(row)
        return board
    except Exception:
        st.error("Board düzeni formatı hatalı. Lütfen kontrol edin.")
        return None

def get_energy_from_level(level_number):
    if str(level_number).endswith('9'): return 5
    if str(level_number).endswith('5'): return 3
    return 1

def count_newly_semi_opened(board, r, c):
    count = 0
    for r_off, c_off in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + r_off, c + c_off
        if 0 <= nr < len(board) and 0 <= nc < len(board[0]) and board[nr][nc]['state'] == 'closed':
            count += 1
    return count

def find_best_strategic_move(board):
    open_items = {}
    semi_open_items = {}
    for r in range(len(board)):
        for c in range(len(board[0])):
            cell = board[r][c]
            if cell['level'] > 0:
                if cell['state'] == 'open':
                    if cell['level'] not in open_items: open_items[cell['level']] = []
                    open_items[cell['level']].append((r, c))
                elif cell['state'] == 'semi-open':
                    if cell['level'] not in semi_open_items: semi_open_items[cell['level']] = []
                    semi_open_items[cell['level']].append((r, c))

    for level in sorted(open_items.keys(), reverse=True):
        if level in semi_open_items and open_items.get(level):
            best_dest = max(semi_open_items[level], key=lambda pos: count_newly_semi_opened(board, pos[0], pos[1]))
            source = open_items[level][0]
            return {'source': source, 'dest': best_dest}

    for level in sorted(open_items.keys(), reverse=True):
        if len(open_items.get(level, [])) >= 2:
            candidates = open_items[level]
            best_dest = max(candidates, key=lambda pos: count_newly_semi_opened(board, pos[0], pos[1]))
            source = None
            for pos in candidates:
                if pos != best_dest:
                    source = pos
                    break
            return {'source': source, 'dest': best_dest}

    return None

def find_empty_open_spots(board):
    return [(r, c) for r in range(len(board)) for c in range(len(board[0])) if board[r][c]['level'] == 0 and board[r][c]['state'] == 'open']

def run_simulation(probabilities, start_level_param, target_level, initial_board):
    board = copy.deepcopy(initial_board)
    current_level = start_level_param - 1
    total_energy = 0

    max_achieved = 0
    for row in board:
        for cell in row:
            if cell['state'] != 'closed' and cell['level'] > max_achieved:
                max_achieved = cell['level']

    milestones = {}
    if max_achieved > 0:
        milestones = {lvl: "Başlangıç" for lvl in range(1, max_achieved + 1)}

    while True:
        best_move = find_best_strategic_move(board)
        if not best_move: break

        source_pos, dest_pos = best_move['source'], best_move['dest']
        board[dest_pos[0]][dest_pos[1]]['level'] += 1
        board[source_pos[0]][source_pos[1]]['level'] = 0
        board[dest_pos[0]][dest_pos[1]]['state'] = 'open'
        r_dest, c_dest = dest_pos
        for r_off, c_off in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r_dest + r_off, c_dest + c_off
            if 0 <= nr < len(board) and 0 <= nc < len(board[0]) and board[nr][nc]['state'] == 'closed':
                board[nr][nc]['state'] = 'semi-open'

        new_max = board[dest_pos[0]][dest_pos[1]]['level']
        if new_max > max_achieved:
            max_achieved = new_max
            if max_achieved not in milestones: milestones[max_achieved] = start_level -1

    last_gen_was_l2 = False
    current_l2_prob = 0.0
    safety_break = 0

    while max_achieved < target_level:
        safety_break += 1
        if safety_break > MAX_LOOPS: return current_level, milestones, board, "TIMEOUT"

        current_level += 1
        total_energy += get_energy_from_level(current_level)

        empty_spots = find_empty_open_spots(board)
        if total_energy > 0 and empty_spots:
            num_to_generate = min(total_energy, len(empty_spots))
            for _ in range(num_to_generate):
                gen_level = 1
                can_gen_l2 = max_achieved >= 5 and not last_gen_was_l2
                if can_gen_l2:
                    current_l2_prob = probabilities.get(max_achieved, current_l2_prob)
                    if random.random() < current_l2_prob: gen_level = 2

                current_empty_spots = find_empty_open_spots(board)
                if not current_empty_spots: break

                spot_to_place = random.choice(current_empty_spots)
                board[spot_to_place[0]][spot_to_place[1]]['level'] = gen_level
                total_energy -= 1
                if gen_level == 2:
                    last_gen_was_l2 = True
                    current_l2_prob = probabilities.get(max_achieved, 0.0)
                else:
                    last_gen_was_l2 = False
                    if max_achieved >= 5: current_l2_prob = min(current_l2_prob + 0.10, 1.0)

        while True:
            best_move = find_best_strategic_move(board)
            if not best_move: break

            source_pos, dest_pos = best_move['source'], best_move['dest']
            board[dest_pos[0]][dest_pos[1]]['level'] += 1
            board[source_pos[0]][source_pos[1]]['level'] = 0
            board[dest_pos[0]][dest_pos[1]]['state'] = 'open'
            r_dest, c_dest = dest_pos
            for r_off, c_off in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r_dest + r_off, c_dest + c_off
                if 0 <= nr < len(board) and 0 <= nc < len(board[0]) and board[nr][nc]['state'] == 'closed':
                    board[nr][nc]['state'] = 'semi-open'

            new_max = board[dest_pos[0]][dest_pos[1]]['level']
            if new_max > max_achieved:
                max_achieved = new_max
                if max_achieved not in milestones: milestones[max_achieved] = current_level

        if not find_best_strategic_move(board) and not find_empty_open_spots(board) and total_energy > 0:
            return current_level, milestones, board, "GRIDLOCKED"

    return current_level, milestones, board, "SUCCESS"

# --- Ana Kod Bloğu ---
initial_board = parse_board_from_text(board_text_input)
if initial_board:
    # --- YENİ EKLENEN KISIM: SİMÜLASYON KURALLARI ---
    st.subheader("📜 Event Mekanikleri")
    st.markdown("""
    1.  **Merge:** Aynı seviyeden 2 element birleşerek bir üst seviye element oluşturur.
    2.  **Enerji:** Bölüm geçerek enerji kazanılır. Enerji, element üretmek için kullanılır (1 enerji = 1 element).
        - Normal Bölüm: **1 Enerji**
        - 'Hard' Bölüm: **3 Enerji**
        - 'Super Hard' Bölüm: **5 Enerji**
    3.  **Element Üretimi (Generator):**
        - Başlangıçta sadece **Seviye 1** element üretir.
        - Oyuncu **5. seviye elementi** oluşturduğunda, **Seviye 2** element üretme şansı açılır.
        - Seviye 2 element gelmediği her üretimde, bir sonraki üretim için Seviye 2 gelme olasılığı **%10 artar**.
        - Üst üste iki kere Seviye 2 element gelemez.
    """)
    st.markdown("---")

    if st.button("🚀 Simülasyonu Başlat!"):
        with st.spinner("Simülasyon çalışıyor..."):
            result_level, result_milestones, final_board, status = run_simulation(initial_probs_float, start_level, max_element_level, initial_board)

        if status == "SUCCESS":
            st.success("🎉 Simülasyon Başarıyla Tamamlandı!")
            col1, col2 = st.columns(2)
            with col1: st.metric(label=f"Hedefe Ulaşılan Bölüm", value=f"{result_level}")
            with col2: st.metric(label="Oynanan Toplam Bölüm Sayısı", value=f"{result_level - start_level + 1}")
        elif status == "GRIDLOCKED":
            st.error(f"SİMÜLASYON DURDURULDU (Gridlock)")
            st.warning(f"Simülasyon **{result_level}. bölümde** kilitlendi.")
        elif status == "TIMEOUT":
            st.error(f"SİMÜLASYON DURDURULDU (Zaman Aşımı)")
            st.warning(f"Simülasyon, {MAX_LOOPS} bölümden uzun sürdüğü için güvenlik amacıyla durduruldu.")

        st.subheader("📊 Element Milestones")
        if result_milestones:
            milestone_df = pd.DataFrame(sorted(result_milestones.items()), columns=["Ulaşılan Element Seviyesi", "Ulaşıldığı Bölüm"])
            st.dataframe(milestone_df, use_container_width=True, hide_index=True)

        st.subheader("🏁 Final Board Görünümü")
        display_data = [[f"L{cell['level']}" if cell['level'] > 0 else "" for cell in row] for row in final_board]
        df = pd.DataFrame(display_data)

        # --- YENİ EKLENEN KISIM: GÜNCELLENMİŞ RENKLENDİRME ---
        def style_board(cell_value, r, c, board_state):
            state = board_state[r][c]['state']
            level = int(cell_value.replace('L', '')) if 'L' in cell_value else 0

            if state == 'closed':
                return 'background-color: #111827; color: #4b5563; border: 1px dashed #4b5563;'
            if state == 'semi-open':
                return 'background-color: #854d0e; color: #fefce8; border: 1px solid #ca8a04;'

            # Tam-Açık kareler
            if level > 0: # Dolu ve Açık
                return 'background-color: #166534; color: #dcfce7; border: 1px solid #22c55e;'
            else: # Boş ve Açık
                return 'background-color: #374151; color: #9ca3af; border: 1px solid #6b7280;'

        final_df_styled = df.style.apply(lambda s: [style_board(s.iloc[c], s.name, c, final_board) for c in range(len(s))], axis=1)
        st.dataframe(final_df_styled, use_container_width=True)

        # --- YENİ EKLENEN KISIM: GÜNCELLENMİŞ RENK KILAVUZU ---
        with st.expander("🎨 Renk Kılavuzu (Anlamları)"):
            st.markdown("""
                - <span style="display:inline-block; width:12px; height:12px; background-color:#166534; border:1px solid #22c55e; vertical-align: middle;"></span> **Yeşil**: Açık ve Dolu Kare
                - <span style="display:inline-block; width:12px; height:12px; background-color:#374151; border:1px solid #6b7280; vertical-align: middle;"></span> **Gri**: Açık ve Boş Kare
                - <span style="display:inline-block; width:12px; height:12px; background-color:#854d0e; border:1px solid #ca8a04; vertical-align: middle;"></span> **Kahverengi**: Yarı-Açık Kare
                - <span style="display:inline-block; width:12px; height:12px; background-color:#111827; border:1px dashed #4b5563; vertical-align: middle;"></span> **Siyah**: Kapalı Kare
            """, unsafe_allow_html=True)
