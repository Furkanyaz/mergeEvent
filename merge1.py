import streamlit as st
import random
import pandas as pd

# Streamlit sayfa yapılandırması
st.set_page_config(page_title="Merge Event Simülasyonu", layout="wide")

# --- Arayüz (UI) ---
st.title("🧩 Merge Event Simülasyonu")
st.markdown("""
Bu simülasyon, bir merge eventinde bir kullanıcının herhangi bir elemente ulaşmak için kaç bölüm oynaması gerektiğini tahmin eder.

**Event Mekanikleri:**
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

# --- Kenar Çubuğu (Sidebar) Parametreleri ---
st.sidebar.header("⚙️ Simülasyon Parametreleri")

st.sidebar.markdown("Buradaki değerleri değiştirerek farklı senaryoları test edebilirsiniz.")
# YENİ: Maksimum element seviyesi ayarı
max_element_level = st.sidebar.number_input(" Element Sayısı", min_value=3, value=12, step=1)

start_level = st.sidebar.number_input("Başlangıç Seviyesi", min_value=1, value=1, step=1)

st.sidebar.subheader("🎁 Element Bonus")
gift_elements_config = {}
# Hediye ayarları artık dinamik olarak max seviyeye kadar oluşturuluyor
for i in range(1, max_element_level + 1):
    gift_elements_config[i] = st.sidebar.number_input(f"Seviye {i} için Bonus", min_value=0, value=0, step=1, key=f"gift_{i}")

st.sidebar.markdown("---")

st.sidebar.subheader(" L2 Üretim Olasılıkları")
initial_probs = {}
# Olasılık ayarları artık dinamik olarak max seviyeden bir öncesine kadar oluşturuluyor
for i in range(5, max_element_level):
    # Örnek varsayılan değerler atıyoruz, isterseniz değiştirebilirsiniz
    default_prob = min(5 + (i - 5) * 5, 30)
    initial_probs[i] = st.sidebar.slider(f"Level {i}'e Ulaşılınca (%)", 0, 100, default_prob, 1, key=f"prob_{i}")

initial_probs_float = {level: prob / 100.0 for level, prob in initial_probs.items()}

# --- Simülasyon Fonksiyonları ---

def get_energy_from_level(level_number):
    if str(level_number).endswith('9'): return 5
    if str(level_number).endswith('5'): return 3
    return 1

def process_merges_and_gifts(elements, max_achieved, milestones, current_lvl, pending_gifts, gift_log):
    action_occurred = True
    while action_occurred:
        action_occurred = False

        for i in range(len(elements) - 1):
            if elements[i] >= 2:
                action_occurred = True
                new_higher_elements = elements[i] // 2
                elements[i+1] += new_higher_elements
                elements[i] %= 2

                achieved_level = i + 2
                if achieved_level > max_achieved:
                    max_achieved = achieved_level
                    if max_achieved not in milestones:
                        milestones[max_achieved] = current_lvl

                    if max_achieved in pending_gifts and pending_gifts[max_achieved] > 0:
                        gift_quantity = pending_gifts[max_achieved]
                        elements[max_achieved - 1] += gift_quantity
                        pending_gifts.pop(max_achieved) # Hediyeyi bir daha vermemek için listeden çıkar

    return elements, max_achieved, milestones, pending_gifts, gift_log

def run_simulation(probabilities, start_level_param, gifts_config, target_level):
    elements = [0] * target_level # Envanter boyutu artık dinamik
    current_level = start_level_param - 1
    total_energy = 0
    max_element_achieved = 0
    last_generated_was_l2 = False
    milestones = {}
    pending_gifts = gifts_config.copy()
    gift_log = []

    current_l2_probability = 0.0

    # Hedef endeksi: target_level - 1
    target_index = target_level - 1

    while elements[target_index] == 0:
        current_level += 1
        total_energy += get_energy_from_level(current_level)

        while total_energy > 0:
            if elements[target_index] > 0: break
            total_energy -= 1

            generated_element_level = 1
            can_generate_l2 = max_element_achieved >= 5 and not last_generated_was_l2

            if can_generate_l2 and random.random() < current_l2_probability:
                generated_element_level = 2

            if generated_element_level == 2:
                elements[1] += 1
                last_generated_was_l2 = True
                current_l2_probability = probabilities.get(max_element_achieved, probabilities.get(target_level - 1, 0.3))
            else:
                elements[0] += 1
                last_generated_was_l2 = False
                if max_element_achieved >= 5:
                    current_l2_probability = min(current_l2_probability + 0.10, 1.0)

            elements, max_element_achieved, milestones, pending_gifts, gift_log = process_merges_and_gifts(
                elements, max_element_achieved, milestones, current_level, pending_gifts, gift_log
            )

            if max_element_achieved >= 5 and generated_element_level == 2:
                current_l2_probability = probabilities.get(max_element_achieved, probabilities.get(target_level - 1, 0.3))

    if target_level not in milestones:
        milestones[target_level] = current_level

    return current_level, milestones, gift_log

# --- Simülasyonu Çalıştırma ---

if st.button("🚀 Simülasyonu Başlat!"):
    with st.spinner("Simülasyon çalışıyor, lütfen bekleyin..."):
        # run_simulation fonksiyonuna yeni max_element_level parametresini iletiyoruz
        result_level, result_milestones, result_gift_log = run_simulation(
            initial_probs_float, start_level, gift_elements_config, max_element_level
        )

    st.success("🎉 Simülasyon Tamamlandı!")

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label=f"{start_level}. Hedefe Ulaşıldığında bulunulan bölüm", value=f"{result_level}")
    with col2:
        st.metric(label="Oynanan Toplam Bölüm Sayısı", value=f"{result_level - start_level + 1}")

    if result_gift_log:
        for log_entry in result_gift_log:
            st.info(log_entry)

    st.subheader("📊 Element Milestones")
    st.markdown("Her bir element seviyesine ilk kez hangi bölümde ulaşıldığının tablosu.")
    if result_milestones:
        milestone_df = pd.DataFrame(result_milestones.items(), columns=["Ulaşılan Element Seviyesi", "Ulaşıldığı Bölüm"])
        st.dataframe(milestone_df, use_container_width=True, hide_index=True)
