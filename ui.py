import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from inference_engine import MesinInferensi


class AntarmukaDiagnosaCupang:
    """Antarmuka pengguna untuk sistem pakar diagnosa penyakit ikan cupang."""

    def __init__(self, root):
        self.root = root
        self.root.title("Sistem Pakar Diagnosa Penyakit Ikan Cupang")
        self.root.geometry("1100x720")
        self.root.minsize(1100, 720)
        self.root.configure(bg="#f0f9ff")

        try:
            self.mesin = MesinInferensi('rules.json')
        except FileNotFoundError:
            messagebox.showerror("Kesalahan", "File rules.json tidak ditemukan!")
            self.root.destroy()
            return

        self.gejala_terpilih = {}
        self.tampilkan_halaman_diagnosa()

    # ================= HALAMAN DIAGNOSA =================
    def tampilkan_halaman_diagnosa(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self._tampilkan_header()
        self._tampilkan_info()
        self._tampilkan_daftar_gejala()
        self._tampilkan_tombol_proses()

    def _tampilkan_header(self):
        frame = tk.Frame(self.root, bg="#0284c7", height=90)
        frame.pack(fill=tk.X)
        frame.pack_propagate(False)
        tk.Label(frame, text="🐠 SISTEM PAKAR DIAGNOSA PENYAKIT IKAN CUPANG",
                 font=("Segoe UI", 18, "bold"), bg="#0284c7", fg="white").pack(pady=6)
        tk.Label(frame, text="Metode Forward Chaining & Certainty Factor",
                 font=("Segoe UI", 10), bg="#0284c7", fg="#bae6fd").pack()
        tk.Label(frame, text="Referensi: Devandi & Wulandari (2024) — Remake oleh Aisyah & Ilmi (2025)",
                 font=("Segoe UI", 8, "italic"), bg="#0284c7", fg="#e0f2fe").pack()

    def _tampilkan_info(self):
        frame = tk.Frame(self.root, bg="#e0f7fa", padx=20, pady=12)
        frame.pack(fill=tk.X, padx=25, pady=(15, 10))
        tk.Label(frame, text="📋 Petunjuk: Pilih gejala yang dialami ikan cupang Anda, lalu tentukan tingkat keyakinan Anda.",
                 font=("Segoe UI", 10), bg="#e0f7fa", fg="#0c4a6e", wraplength=1000, justify=tk.LEFT).pack(anchor=tk.W)

    def _tampilkan_daftar_gejala(self):
        main_frame = tk.Frame(self.root, bg="#f0f9ff")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)

        canvas = tk.Canvas(main_frame, bg="#f0f9ff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f9ff")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollable_frame.columnconfigure(0, weight=1)

        self.gejala_terpilih = {}
        for idx, (kode, teks_gejala) in enumerate(self.mesin.gejala.items()):
            self._buat_kartu_gejala(scrollable_frame, kode, teks_gejala, idx)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _buat_kartu_gejala(self, parent, kode, teks, baris):
        card = tk.Frame(parent, bg="white", relief=tk.GROOVE, borderwidth=1,
                        highlightbackground="#bae6fd", highlightthickness=1)
        card.grid(row=baris, column=0, sticky="ew", padx=8, pady=6, ipadx=5)
        card.columnconfigure(1, weight=1)

        tk.Label(card, text=kode, font=("Segoe UI", 9, "bold"), bg="#bae6fd", fg="#0e7490",
                 width=6, padx=10, pady=8).grid(row=0, column=0, padx=8, pady=6, sticky="w")
        tk.Label(card, text=teks, font=("Segoe UI", 11), bg="white", fg="#0f172a",
                 anchor="w", wraplength=800, justify=tk.CENTER).grid(row=0, column=1, padx=8, pady=6, sticky="w")

        frame_opsi = tk.Frame(card, bg="white")
        frame_opsi.grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")

        var = tk.DoubleVar(value=0.0)
        self.gejala_terpilih[kode] = var

        for i, (label, nilai) in enumerate(self.mesin.cf_pengguna.items()):
            rb = tk.Radiobutton(frame_opsi, text=label, variable=var, value=nilai,
                                font=("Segoe UI", 9), bg="white", fg="#334155",
                                selectcolor="#e0f2fe", indicatoron=True,
                                padx=6, pady=2, highlightthickness=0)
            rb.grid(row=0, column=i, padx=4, pady=2, sticky="w")

    def _tampilkan_tombol_proses(self):
        frame = tk.Frame(self.root, bg="#f0f9ff", pady=15)
        frame.pack(fill=tk.X, padx=20)
        tk.Button(frame, text="🔍 PROSES DIAGNOSA", font=("Segoe UI", 12, "bold"),
                  bg="#0284c7", fg="white", padx=25, pady=12,
                  cursor="hand2", relief=tk.FLAT, borderwidth=0,
                  command=self._proses_diagnosa).pack()

    # ================= HALAMAN HASIL =================
    def _proses_diagnosa(self):
        gejala_pengguna = {k: v.get() for k, v in self.gejala_terpilih.items() if v.get() > 0}
        if not gejala_pengguna:
            messagebox.showwarning("Peringatan", "Silakan pilih minimal satu gejala dengan keyakinan positif!")
            return

        hasil = self.mesin.forward_chaining(gejala_pengguna)
        if hasil:
            self.tampilkan_halaman_hasil(hasil, gejala_pengguna)
        else:
            messagebox.showinfo("Hasil Diagnosa", "Tidak ditemukan penyakit yang sesuai.")

    def tampilkan_halaman_hasil(self, hasil_list, gejala_pengguna):
        for widget in self.root.winfo_children():
            widget.destroy()

        self._tampilkan_header_hasil()

        # Scrollable container
        konten = tk.Frame(self.root, bg="#f0f9ff")
        konten.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)

        canvas = tk.Canvas(konten, bg="#f0f9ff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(konten, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f9ff")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for idx, hasil in enumerate(hasil_list):
            self._buat_card_hasil(scrollable_frame, hasil, idx)

        self._kartu_gejala_terdeteksi(scrollable_frame, gejala_pengguna)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._tombol_hasil()

    def _tampilkan_header_hasil(self):
        frame = tk.Frame(self.root, bg="#0284c7", height=90)
        frame.pack(fill=tk.X)
        frame.pack_propagate(False)
        tk.Label(frame, text="📊 HASIL DIAGNOSA", font=("Segoe UI", 18, "bold"),
                 bg="#0284c7", fg="white").pack(pady=10)
        tk.Label(frame, text="Sistem Pakar Penyakit Ikan Cupang",
                 font=("Segoe UI", 10), bg="#0284c7", fg="#cffafe").pack()

    def _buat_card_hasil(self, parent, hasil, idx):
        card = tk.Frame(parent, bg="white", relief=tk.SOLID, borderwidth=1)
        card.pack(fill=tk.X, pady=20)

        tk.Label(card, text=f"{idx+1}. 🦠 {hasil['nama']} ({hasil['kode']})",
                 font=("Segoe UI", 13, "bold"), bg="white", fg="#0e7490").pack(anchor=tk.W, padx=14, pady=(10, 2))
        tk.Label(card, text=f"Tingkat Kepastian: {hasil['persentase_cf']:.1f}%",
                 font=("Segoe UI", 11, "bold"), bg="white", fg="#0891b2").pack(anchor=tk.W, padx=14)
        ttk.Progressbar(card, length=1150, mode='determinate',
                        value=hasil['persentase_cf']).pack(fill=tk.X, padx=14, pady=(6, 10))

        if hasil.get('deskripsi'):
            tk.Label(card, text=hasil['deskripsi'], font=("Segoe UI", 10),
                     bg="white", fg="#475569", wraplength=950, justify=tk.LEFT).pack(anchor=tk.W, padx=14, pady=(0, 8))

        # langsung tampilkan pengobatan & pencegahan
        rec = tk.Frame(card, bg="#fff7ed")
        rec.pack(fill=tk.X, padx=14, pady=(0, 10))
        tk.Label(rec, text="💊 Pengobatan", font=("Segoe UI", 10, "bold"),
                 bg="#fff7ed", fg="#92400e").pack(anchor=tk.W, padx=6, pady=(6, 2))
        tk.Label(rec, text=hasil.get('pengobatan', 'Tidak ada rekomendasi.'),
                 bg="#fff7ed", fg="#78350f", font=("Segoe UI", 9),
                 wraplength=950, justify=tk.LEFT).pack(anchor=tk.W, padx=6, pady=(0, 4))
        tk.Label(rec, text="🛡️ Pencegahan", font=("Segoe UI", 10, "bold"),
                 bg="#fff7ed", fg="#92400e").pack(anchor=tk.W, padx=6, pady=(4, 2))
        tk.Label(rec, text=hasil.get('pencegahan', '-'),
                 bg="#fff7ed", fg="#78350f", font=("Segoe UI", 9),
                 wraplength=950, justify=tk.LEFT).pack(anchor=tk.W, padx=6, pady=(0, 6))

    def _kartu_gejala_terdeteksi(self, parent, gejala_pengguna):
        card = tk.Frame(parent, bg="white", relief=tk.SOLID, borderwidth=1)
        card.pack(fill=tk.BOTH, expand=True, pady=8)
        tk.Label(card, text="✓ Gejala yang Terdeteksi", font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#0e7490").pack(anchor=tk.W, padx=18, pady=(10, 5))
        box = scrolledtext.ScrolledText(card, height=6, font=("Segoe UI", 9),
                                        bg="#f8fafc", relief=tk.FLAT, padx=8, pady=6)
        box.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 10))
        for kode, cf in gejala_pengguna.items():
            nama = self.mesin.gejala.get(kode, 'Tidak diketahui')
            box.insert(tk.END, f"{kode} - {nama}\n   Keyakinan: {cf*100:.0f}%\n\n")
        box.config(state=tk.DISABLED)

    def _tombol_hasil(self):
        frame = tk.Frame(self.root, bg="#f0f9ff", pady=15)
        frame.pack(fill=tk.X, padx=20)
        tk.Button(frame, text="🔄 Diagnosa Ulang", font=("Segoe UI", 10, "bold"),
                  bg="white", fg="#0284c7", padx=20, pady=8,
                  relief=tk.SOLID, borderwidth=2, cursor="hand2",
                  command=self.tampilkan_halaman_diagnosa).pack(side=tk.LEFT, padx=4)
        tk.Button(frame, text="❌ Keluar", font=("Segoe UI", 10, "bold"),
                  bg="#ef4444", fg="white", padx=20, pady=8,
                  relief=tk.FLAT, cursor="hand2",
                  command=self.root.destroy).pack(side=tk.RIGHT, padx=4)


def main():
    root = tk.Tk()
    app = AntarmukaDiagnosaCupang(root)
    root.mainloop()


if __name__ == "__main__":
    main()
