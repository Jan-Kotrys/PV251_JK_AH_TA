import pandas as pd
import json

# nacteni data framu
df = pd.read_csv("../data_raw/Otevrena-data-NR-11-01-potraty-sociodemograficke-charakteristiky.csv", sep=",")


# jednotlive slovniky pro mapovani stringu k num hodnotam
druh_potratu_map = {
    1: "Spontánní",
    2: "Ektopické těhotenství",
    3: "UPT",
    4: "Ostatní"
}

vzdelani_map = {
    1: "Základní neukončené",
    2: "Základní ukončené",
    3: "Střední odborné",
    4: "Úplné střední odborné",
    5: "Úplné střední všeobecné",
    6: "Bakalářské",
    7: "Vysokoškolské",
    0: "Nezjištěno",
}

rodinny_stav_map = {
    1: "Svobodná",
    2: "Vdaná",
    3: "Rozvedená",
    4: "Ovdovělá",
    5: "Družka",
    0: "Nezjištěno"
}

stari_plodu_map = {
    1: "do 8. tt",
    2: "9.-12. tt",
    3: "13.-24. tt",
    4: "nad 24. tt"
}

cizinka_map = {
    0: "Češka",
    1: "Cizinka"
}

# apply jednotlive mapovani
df["druh_potratu_text"] = df["druh_potratu"].map(druh_potratu_map)
df["vzdelani_text"] = df["vzdelani"].map(vzdelani_map)
df["rodinny_stav_text"] = df["rodinny_stav"].map(rodinny_stav_map)
df["stari_plodu_text"] = df["stari_plodu"].map(stari_plodu_map)
df["obcanstvi_text"] = df["statni_obcanstvi_cizinka"].map(cizinka_map)

# decoding veku zeny
def decode_age(val):
    val_str = str(val)
    if len(val_str) == 8:
        # 1. Ošetření případu "méně než 19" (končí na 0019)
        if val_str[4:8] == "0019":
            return "Méně než 19 let"
        
        od_veku = int(val_str[4:6])
        do_veku = int(val_str[6:8])
        
        # 2. Ošetření případu "více než 40" (např. pokud horní hranice nedává smysl nebo je 99)
        if od_veku == 40 and (do_veku == 0 or do_veku == 99):
            return "Více než 40 let"
            
        return f"{od_veku}-{do_veku} let"
        
    return "Neznámý věk"

# apply dekodovani veku zeny 
df["vek_kategorie"] = df["vek_zeny"].apply(decode_age)

# Oriznuti dlouheho id v jsonu (v csv je length 5)
df["kraj_id"] = df["kraj_bydliste"].astype(str).str[:5]

# --- T1: Věková distribuce v čase ---
# Počty případů pro každou věkovou skupinu v jednotlivých letech
t1_data = df.groupby(["rok_potratu", "vek_kategorie"]).size().unstack(fill_value=0).to_dict(orient="index")
with open("../data_clean/t1_age.json", "w", encoding="utf-8") as f:
    json.dump(t1_data, f, ensure_ascii=False, indent=2)

# --- T2: Socioekonomické profily ---
# Vzdělání x Rodinný stav x Počet předchozích UPT
t2_data = df.groupby(["vzdelani_text", "rodinny_stav_text", "pocet_predch_UPT"]).size().reset_index(name="pocet")
t2_data.to_json("../data_clean/t2_profiles.json", orient="records", force_ascii=False, indent=2)

# --- T3 & T6: Regionální data pro mapu a trendy (Kraj x Rok) ---
t3_t6_data = {}
for (kraj, rok), group in df.groupby(["kraj_id", "rok_potratu"]):
    if kraj not in t3_t6_data:
        t3_t6_data[kraj] = {}
    
    counts = group["druh_potratu_text"].value_counts().to_dict()
    upt = counts.get("Umělé přerušení těhotenství (UPT)", 0)
    spont = counts.get("Spontánní", 0)
    ratio = round(upt / spont, 2) if spont > 0 else 0
    
    t3_t6_data[kraj][str(rok)] = {
        "celkem": int(len(group)),
        "upt": int(upt),
        "spontanni": int(spont),
        "ostatni": int(counts.get("Ostatní", 0) + counts.get("Ektopické těhotenství", 0)),
        "ratio_upt_spont": ratio
    }

with open("../data_clean/t3_t6_regional.json", "w", encoding="utf-8") as f:
    json.dump(t3_t6_data, f, ensure_ascii=False, indent=2)

# --- T4: Stáří plodu vs Reprodukční historie ---
t4_data = df.groupby(["stari_plodu_text", "pocet_predch_UPT", "pocet_predch_spont_potratu"]).size().reset_index(name="pocet")
t4_data.to_json("../data_clean/t4_gestation.json", orient="records", force_ascii=False, indent=2)

# --- T5: Občanství vs Druh potratu ---
t5_data = df.groupby(["obcanstvi_text", "druh_potratu_text"]).size().unstack(fill_value=0).to_dict(orient="index")
with open("../data_clean/t5_citizenship.json", "w", encoding="utf-8") as f:
    json.dump(t5_data, f, ensure_ascii=False, indent=2)

        
    


