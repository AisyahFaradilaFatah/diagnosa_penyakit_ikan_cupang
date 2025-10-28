# inference_engine.py
import json
from typing import Dict, List


class MesinInferensi:
    
    def __init__(self, file_aturan='rules.json'):
        with open(file_aturan, 'r', encoding='utf-8') as f:
            self.kb = json.load(f)

        self.gejala = self.kb.get('gejala', {})
        self.penyakit = self.kb.get('penyakit', {})
        self.aturan = self.kb.get('aturan', [])
        self.cf_pengguna = self.kb.get('cf_pengguna', {})

        # Pisahkan aturan primary dan sekuensial
        self.aturan_primary = []
        self.aturan_sekuensial = []
        for rule in self.aturan:
            # Deteksi sekuensial: jika ada premis yang dimulai dengan "P"
            if any(isinstance(p, str) and p.startswith("P") for p in rule.get("if", [])):
                self.aturan_sekuensial.append(rule)
            else:
                self.aturan_primary.append(rule)

    def hitung_cf_tunggal(self, cf_pakar: float, cf_user: float) -> float:
        """CF(H,E) = CF_pakar × CF_user"""
        return cf_pakar * cf_user

    def gabung_cf(self, cf1: float, cf2: float) -> float:
        """CF_gabungan = CF1 + CF2 × (1 - CF1)
        Asumsi: cf1 dan cf2 berada di rentang [0,1]
        """
        return cf1 + cf2 * (1 - cf1)

    def hitung_cf_penyakit(self, rule: Dict, fakta: Dict[str, float]) -> tuple:
        """
        Hitung CF untuk satu aturan.
        Perubahan: proses semua premis (AND) tapi jika premis tidak ada di fakta,
        gunakan cf_user = 0.0 sehingga rule tetap menghasilkan CF parsial.
        """
        cf_gabungan = 0.0
        langkah = []

        for premis in rule.get("if", []):
            cf_pakar = rule.get("cf_expert", {}).get(premis, 0.0)
            cf_user = fakta.get(premis, 0.0)  # default 0.0 jika premis tidak ada
            cf_tunggal = self.hitung_cf_tunggal(cf_pakar, cf_user)

            langkah.append({
                "premis": premis,
                "cf_pakar": cf_pakar,
                "cf_user": cf_user,
                "cf_tunggal": cf_tunggal
            })

            if cf_gabungan == 0:
                cf_gabungan = cf_tunggal
            else:
                cf_gabungan = self.gabung_cf(cf_gabungan, cf_tunggal)

        return cf_gabungan, langkah

    def forward_chaining(self, gejala_user: Dict[str, float], verbose: bool = False) -> List[Dict]:
        """Forward Chaining dengan multi-level, mengembalikan semua penyakit terdeteksi."""
        fakta = dict(gejala_user)
        hasil_diagnosa = {}
        rules_executed = set()  # track rule yang sudah dijalankan

        if verbose:
            print("\n" + "=" * 70)
            print("FORWARD CHAINING - MULTI LEVEL INFERENSI")
            print("=" * 70)
            print(f"Input gejala: {list(gejala_user.keys())}\n")

        # Iterasi maksimal 10 kali untuk chaining multi-level
        for iterasi in range(1, 11):
            fakta_baru = False

            if verbose:
                print(f"{'-' * 70}")
                print(f"ITERASI {iterasi}")
                print('-' * 70)

            
            # TAHAP 1: EVALUASI ATURAN PRIMARY
            
            if verbose:
                print("\n▶ Aturan Primary (Gejala → Penyakit):")

            for rule in self.aturan_primary:
                rule_id = rule.get("id")
                kode_penyakit = rule.get("penyakit_kode") or rule.get("then")

                # Skip jika rule sudah dijalankan
                if rule_id in rules_executed:
                    continue

                cf_hasil, langkah = self.hitung_cf_penyakit(rule, fakta)

                # Simpan jika ada kontribusi (lebih besar dari 0)
                if cf_hasil > 0:
                    if verbose:
                        print(f"  • Rule {rule_id}: {kode_penyakit} → CF = {cf_hasil:.4f}")

                    if kode_penyakit in hasil_diagnosa:
                        # gabungkan paralel
                        cf_lama = hasil_diagnosa[kode_penyakit]["cf"]
                        cf_baru = self.gabung_cf(cf_lama, cf_hasil)
                        hasil_diagnosa[kode_penyakit]["cf"] = cf_baru
                        hasil_diagnosa[kode_penyakit]["langkah"].extend(langkah)
                        hasil_diagnosa[kode_penyakit]["rule_id"] += f", {rule_id}"
                        fakta[kode_penyakit] = cf_baru
                    else:
                        hasil_diagnosa[kode_penyakit] = {
                            "cf": cf_hasil,
                            "langkah": langkah,
                            "rule_id": rule_id
                        }
                        fakta[kode_penyakit] = cf_hasil

                    rules_executed.add(rule_id)
                    fakta_baru = True

            
            # TAHAP 2: EVALUASI ATURAN SEKUENSIAL
            
            if verbose:
                print("\n▶ Aturan Sekuensial (Penyakit → Penyakit):")

            for rule in self.aturan_sekuensial:
                rule_id = rule.get("id")
                kode_penyakit = rule.get("penyakit_kode") or rule.get("then")

                # Skip jika rule sudah dijalankan
                if rule_id in rules_executed:
                    continue

                cf_hasil, langkah = self.hitung_cf_penyakit(rule, fakta)

                if cf_hasil > 0:
                    if verbose:
                        print(f"  • Rule {rule_id}: {kode_penyakit} → CF = {cf_hasil:.4f}")
                        print(f"    Premis: {rule.get('if')}")

                    # Jika sudah ada, gabungkan (paralel)
                    if kode_penyakit in hasil_diagnosa:
                        cf_lama = hasil_diagnosa[kode_penyakit]["cf"]
                        cf_baru = self.gabung_cf(cf_lama, cf_hasil)
                        if verbose:
                            print(f"    ⚡ PARALEL! {cf_lama:.4f} + {cf_hasil:.4f} = {cf_baru:.4f}")
                        hasil_diagnosa[kode_penyakit]["cf"] = cf_baru
                        hasil_diagnosa[kode_penyakit]["langkah"].extend(langkah)
                        hasil_diagnosa[kode_penyakit]["rule_id"] += f", {rule_id}"
                        fakta[kode_penyakit] = cf_baru
                    else:
                        hasil_diagnosa[kode_penyakit] = {
                            "cf": cf_hasil,
                            "langkah": langkah,
                            "rule_id": rule_id
                        }
                        fakta[kode_penyakit] = cf_hasil

                    rules_executed.add(rule_id)
                    fakta_baru = True

            # Hentikan jika tidak ada fakta baru
            if not fakta_baru:
                if verbose:
                    print(f"\n✓ Tidak ada fakta baru. Inferensi selesai di iterasi {iterasi}.")
                break

        
        # FORMAT HASIL UNTUK UI - kembalikan semua penyakit yang terdeteksi
        
        hasil_final = []
        for kode_penyakit, data in hasil_diagnosa.items():
            info = self.penyakit.get(kode_penyakit, {})
            hasil_final.append({
                "kode": kode_penyakit,
                "nama": info.get("nama", kode_penyakit),
                "cf": data["cf"],
                "persentase_cf": data["cf"] * 100,
                "deskripsi": info.get("deskripsi", ""),
                "pengobatan": info.get("pengobatan", ""),
                "pencegahan": info.get("pencegahan", ""),
                "langkah": data["langkah"],
                "rule_id": data["rule_id"]
            })

        # Urut berdasarkan CF tertinggi dulu
        hasil_final.sort(key=lambda x: x["cf"], reverse=True)

        if verbose:
            print("\n" + "=" * 70)
            print("HASIL AKHIR DIAGNOSA:")
            print("=" * 70)
            for i, hasil in enumerate(hasil_final, 1):
                print(f"{i}. {hasil['nama']} ({hasil['kode']})")
                print(f"   CF: {hasil['cf']:.4f} ({hasil['persentase_cf']:.2f}%)")
                print(f"   Rule: {hasil['rule_id']}")
            print("=" * 70)

        return hasil_final

    def get_nama_gejala(self, kode: str) -> str:
        return self.gejala.get(kode, "Tidak diketahui")

    def get_label_cf(self, nilai_cf: float) -> str:
        for label, nilai in self.cf_pengguna.items():
            if abs(nilai - nilai_cf) < 0.01:
                return label
        return f"CF: {nilai_cf:.2f}"
