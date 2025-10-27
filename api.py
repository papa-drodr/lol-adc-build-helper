import customtkinter as ctk
from PIL import Image

ctk.set_appearance_mode("dark")

root = ctk.CTk()
root.title("상위 1퍼 원딜의 LoL 원딜 빌드 추천기")
root.geometry("600x500")

champions = ["Jinx", "Caitlyn", "Ezreal"]
images = {}

for i, name in enumerate(champions):
    img = Image.open(f"images/{name.lower()}.jpg")
    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 120))
    images[name] = ctk_img  # 참조 유지 (가비지컬렉션 방지)

    btn = ctk.CTkButton(
        root,
        text=name,
        image=ctk_img,
        compound="top",
        width=150,
        height=150,
        command=lambda n=name: print(f"{n} 클릭됨")
    )
    btn.grid(row=i // 3, column=i % 3, padx=15, pady=15)

root.mainloop()
