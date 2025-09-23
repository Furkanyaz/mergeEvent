import streamlit as st
import random
import pandas as pd

# Streamlit sayfa yapılandırması
st.set_page_config(page_title="Merge Oyunu Simülasyonu", layout="wide")

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

st.sidebar.header("⚙️ Simülasyon Parametreleri")
st.sidebar.markdown("Buradaki değerleri değiştirerek farklı senaryoları test edebilirsiniz.")

# Kullanıcının değiştirebileceği başlangıç seviyesi
start_level = st.sidebar.number_input("Başlangıç Seviyesi", min_value=1, value=1, step=1)

st.sidebar.markdown("---") # Ayraç

# Kullanıcının değiştirebileceği başlangıç olasılıkları
initial_probs = {
    5: st.sidebar.slider("Seviye 5'e Ulaşılınca L2 Olasılığı (%)", 0, 100, 5, 1),
    6: st.sidebar.slider("Seviye 6'ya Ulaşılınca L2 Olasılığı (%)", 0, 100, 10, 1),
    7: st.sidebar.slider("Seviye 7'ye Ulaşılınca L2 Olasılığı (%)", 0, 100, 12, 1),
    8: st.sidebar.slider("Seviye 8'e Ulaşılınca L2 Olasılığı (%)", 0, 100, 15, 1),
    9: st.sidebar.slider("Seviye 9'a Ulaşılınca L2 Olasılığı (%)", 0, 100, 20, 1),
    10: st.sidebar.slider("Seviye 10'a Ulaşılınca L2 Olasılığı (%)", 0, 100, 25, 1),
    11: st.sidebar.slider("Seviye 11'e Ulaşılınca L2 Olasılığı (%)", 0, 100, 30, 1),
}

# Olasılıkları 0-1 aralığına çevir
initial_probs_float = {level: prob / 100.0 for level, prob in initial_probs.items()}


# --- Simülasyon Fonksiyonları ---

def get_energy_from_level(level_number):
    """Belirtilen seviyeden kazanılacak enerjiyi döndürür."""
    if str(level_number).endswith('9'):
        return 5
    elif str(level_number).endswith('5'):
        return 3
    else:
        return 1

def run_simulation(probabilities, start_level_param):
    """Ana simülasyon fonksiyonu."""
    elements = [0] * 12
    current_level = start_level_param - 1 # Döngü başında artırılacağı için -1 ile başla
    total_energy = 0
    max_element_achieved = 0
    current_l2_probability = 0.0
    last_generated_was_l2 = False

    milestones = {} # Kilometre taşlarını tutacak dictionary

    while elements[11] == 0:
        current_level += 1
        total_energy += get_energy_from_level(current_level)

        while total_energy > 0:
            total_energy -= 1

            generated_element_level = 1
            can_generate_l2 = max_element_achieved >= 5 and not last_generated_was_l2

            if can_generate_l2:
                if random.random() < current_l2_probability:
                    generated_element_level = 2

            if generated_element_level == 2:
                elements[1] += 1
                last_generated_was_l2 = True
                if max_element_achieved in probabilities:
                    current_l2_probability = probabilities[max_element_achieved]
                else:
                    current_l2_probability = probabilities.get(11, 0.3)
            else:
                elements[0] += 1
                last_generated_was_l2 = False
                if max_element_achieved >= 5:
                    current_l2_probability += 0.10
                    current_l2_probability = min(current_l2_probability, 1.0)

            for i in range(len(elements) - 1):
                if elements[i] >= 2:
                    new_higher_elements = elements[i] // 2
                    elements[i+1] += new_higher_elements
                    elements[i] %= 2

                    # En yüksek element seviyesini kontrol et ve kilometre taşını kaydet
                    # `i+2` yeni ulaşılan seviyeyi temsil eder (örn: i=0 ise L1'ler birleşir L2 olur)
                    if (i + 2) > max_element_achieved:
                        max_element_achieved = i + 2
                        # Daha önce bu seviyeye ulaşılmadıysa kaydet
                        if max_element_achieved not in milestones:
                            milestones[max_element_achieved] = current_level

                        if max_element_achieved in probabilities:
                            current_l2_probability = probabilities[max_element_achieved]

            if elements[11] > 0:
                break

    # Hedef olan 12. seviyeyi de kilometre taşına ekle
    if 12 not in milestones:
        milestones[12] = current_level

    return current_level, milestones

# --- Simülasyonu Çalıştırma ---

if st.button("🚀 Simülasyonu Başlat!"):
    with st.spinner("Simülasyon çalışıyor, lütfen bekleyin..."):
        result_level, result_milestones = run_simulation(initial_probs_float, start_level)

    st.success("🎉 Simülasyon Tamamlandı!")

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label=f"{start_level}. Hedefe Ulaşıldığında bulunulan bölüm",
            value=f"{result_level}"
        )
    with col2:
        st.metric(
            label="Oynanan Toplam Bölüm Sayısı",
            value=f"{result_level - start_level + 1}"
        )

    st.subheader("📊 Element Milestones")
    st.markdown("Her bir element seviyesine ilk kez hangi bölümde ulaşıldığının tablosu.")

    if result_milestones:
        # Dictionary'i DataFrame'e çevirerek daha şık bir tablo oluştur
        milestone_df = pd.DataFrame(result_milestones.items(), columns=["Ulaşılan Element Seviyesi", "Ulaşıldığı Bölüm"])
        st.dataframe(milestone_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Hiçbir şey kaydedilmedi.")