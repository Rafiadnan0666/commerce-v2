from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy import create_engine, Column, String, Float, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import uvicorn
import midtransclient

snap = midtransclient.Snap(
    is_production=False,
    server_key='SB-Mid-server-slQoGh5H1EXGW4kPEwIpYsG_'
)

param = {
    "transaction_details": {
        "order_id": "ORDER-12345",
        "gross_amount": 200000
    },
    "customer_details": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "phone": "+628123456789"
    }
}


transaction = snap.create_transaction(param)

transaction_token = transaction['token']


DATABASE_URL = "mysql+mysqlconnector://root:@localhost:3306/commerce"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


cihuyy = FastAPI()

cihuyy.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    nama: str
    password: str
    alamat: Optional[str] = None
    role: Optional[str] = "pembeli"

class Kategori(BaseModel):
    id: Optional[UUID] = None
    nama_kategori: str

class Barang(BaseModel):
    id: Optional[UUID] = None
    nama: str
    deskripsi: str
    harga: float
    gambar_url: str  
    quantity: int
    kategori_id: UUID
    penjual_id: UUID  

class Pesanan(BaseModel):
    id: Optional[UUID] = None
    pembeli_id: UUID  
    keranjang_id: UUID
    barang_id: UUID 

class Komentar(BaseModel):
    id: Optional[UUID] = None
    teks_komentar: str
    barang_id: UUID
    user_id: UUID
    mention_id: Optional[UUID] = None  

class Keranjang(BaseModel):
    id: Optional[UUID] = None
    barang_id: UUID
    user_id: UUID
    kuantitas: int
class UserModel(Base):
    __tablename__ = 'users'
    id = Column(String(36), primary_key=True, index=True)
    nama = Column(String(50), unique=True, index=True)
    password = Column(String(50))
    alamat = Column(String(255), nullable=True)
    role = Column(String(20), default="pembeli")
    barangs = relationship("BarangModel", back_populates="penjual")

class BarangModel(Base):
    __tablename__ = 'barangs'
    id = Column(String(36), primary_key=True, index=True)
    nama = Column(String(100))
    deskripsi = Column(String(255))
    harga = Column(Float)
    gambar_url = Column(String(255))
    quantity = Column(Integer)
    kategori_id = Column(String(36), ForeignKey('kategoris.id'))
    penjual_id = Column(String(36), ForeignKey('users.id'))
    kategori = relationship("KategoriModel", back_populates="barangs")
    penjual = relationship("UserModel", back_populates="barangs")
    keranjangs = relationship("KeranjangModel", back_populates="barang")

class KategoriModel(Base):
    __tablename__ = 'kategoris'
    id = Column(String(36), primary_key=True, index=True)
    nama_kategori = Column(String(100))

class PesananModel(Base):
    __tablename__ = 'pesanans'
    id = Column(String(36), primary_key=True, index=True)
    pembeli_id = Column(String(36), ForeignKey('users.id'))
    keranjang_id = Column(String(36))
    barang_id = Column(String(36), ForeignKey('barangs.id'))
class KeranjangModel(Base):
    __tablename__ = "keranjangs"
    id = Column(String(36), primary_key=True, index=True)
    barang_id = Column(String(36), ForeignKey('barangs.id'))
    user_id = Column(String(36), ForeignKey('users.id'))
    kuantitas = Column(Integer)
    barang = relationship("BarangModel", back_populates="keranjangs")
    user = relationship("UserModel", back_populates="keranjangs")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@cihuyy.post("/register/")
def register_user(user: User, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.nama == user.nama).first()
    if db_user:
        raise HTTPException(status_code=400, message="User already exists")

    new_user = UserModel(
        id=str(uuid4()),
        nama=user.nama,
        password=user.password,
        alamat=user.alamat,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"user_id": new_user.id, "role": new_user.role}

@cihuyy.get("/users/", response_model=List[User])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(UserModel).all()
    return users


@cihuyy.post("/kategoris/", response_model=Kategori)
def buat_kategori(kategori: Kategori, db: Session = Depends(get_db)):
    new_kategori = KategoriModel(
        id=str(uuid4()),
        nama_kategori=kategori.nama_kategori,
    )
    db.add(new_kategori)
    db.commit()
    db.refresh(new_kategori)
    return new_kategori




@cihuyy.get("/kategoris/", response_model=List[Kategori])
def lihat_semua_kategori(db: Session = Depends(get_db)):
    return db.query(KategoriModel).all()

@cihuyy.post("/barangs/", response_model=Barang)
def buat_barang(barang: Barang, db: Session = Depends(get_db)):
    barang.id = uuid4()
    penjual = db.query(UserModel).filter(UserModel.id == str(barang.penjual_id), UserModel.role == "penjual").first()
    if not penjual:
        raise HTTPException(status_code=404, message="Penjual tidak ditemukan atau tidak terdaftar sebagai penjual")

    new_barang = BarangModel(
        id=str(barang.id),
        nama=barang.nama,
        deskripsi=barang.deskripsi,
        harga=barang.harga,
        gambar_url=barang.gambar_url,
        quantity=barang.quantity,
        kategori_id=str(barang.kategori_id),
        penjual_id=str(barang.penjual_id)
    )
    db.add(new_barang)
    db.commit()
    db.refresh(new_barang)
    return barang

@cihuyy.get("/barangs/", response_model=List[Barang])
def lihat_semua_barang(db: Session = Depends(get_db)):
    return db.query(BarangModel).all()

@cihuyy.get("/barangs/{barang_id}", response_model=Barang)
def lihat_barang(barang_id: UUID, db: Session = Depends(get_db)):
    barang = db.query(BarangModel).filter(BarangModel.id == str(barang_id)).first()
    if not barang:
        raise HTTPException(status_code=404, message="Barang tidak ditemukan")
    return barang

@cihuyy.put("/barangs/{barang_id}", response_model=Barang)
def update_barang(barang_id: UUID, barang_baru: Barang, db: Session = Depends(get_db)):
    barang = db.query(BarangModel).filter(BarangModel.id == str(barang_id)).first()
    if not barang:
        raise HTTPException(status_code=404, message="Barang tidak ditemukan")

    penjual = db.query(UserModel).filter(UserModel.id == str(barang_baru.penjual_id), UserModel.role == "penjual").first()
    if not penjual:
        raise HTTPException(status_code=404, message="Penjual tidak ditemukan atau tidak terdaftar sebagai penjual")

    barang.nama = barang_baru.nama
    barang.deskripsi = barang_baru.deskripsi
    barang.harga = barang_baru.harga
    barang.gambar_url = barang_baru.gambar_url
    barang.quantity = barang_baru.quantity
    barang.kategori_id = str(barang_baru.kategori_id)
    barang.penjual_id = str(barang_baru.penjual_id)
    db.commit()
    db.refresh(barang)
    return barang

@cihuyy.delete("/barangs/{barang_id}")
def hapus_barang(barang_id: UUID, db: Session = Depends(get_db)):
    barang = db.query(BarangModel).filter(BarangModel.id == str(barang_id)).first()
    if not barang:
        raise HTTPException(status_code=404, message="Barang tidak ditemukan")

    db.delete(barang)
    db.commit()
    return {"message": "Barang berhasil dihapus"}




@cihuyy.post("/pesanans/", response_model=Pesanan)
def buat_pesanan(pesanan: Pesanan, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == pesanan.pembeli_id, User.role == "pembeli").first()
    if not user:
        raise HTTPException(status_code=404, message="Pembeli tidak ditemukan atau tidak terdaftar sebagai pembeli")
    
    barang = db.query(Barang).filter(Barang.id == pesanan.barang_id).first()
    if not barang or barang.quantity <= 0:
        raise HTTPException(status_code=404, message="Barang tidak ditemukan atau stok tidak cukup")

    db.add(pesanan)
    db.commit()
    db.refresh(pesanan)
    return pesanan

@cihuyy.get("/pesanans/", response_model=List[Pesanan])
def lihat_semua_pesanan(db: Session = Depends(get_db)):
    return db.query(Pesanan).all()

@cihuyy.get("/pesanans/{pesanan_id}", response_model=Pesanan)
def lihat_pesanan(pesanan_id: UUID, db: Session = Depends(get_db)):
    pesanan = db.query(Pesanan).filter(Pesanan.id == pesanan_id).first()
    if not pesanan:
        raise HTTPException(status_code=404, message="Pesanan tidak ditemukan")
    return pesanan

@cihuyy.delete("/pesanans/{pesanan_id}")
def hapus_pesanan(pesanan_id: UUID, db: Session = Depends(get_db)):
    pesanan = db.query(Pesanan).filter(Pesanan.id == pesanan_id).first()
    if not pesanan:
        raise HTTPException(status_code=404, message="Pesanan tidak ditemukan")
    db.delete(pesanan)
    db.commit()
    return {"message": "Pesanan berhasil dihapus"}


@cihuyy.post("/keranjangs/", response_model=Keranjang)
def buat_keranjang(keranjang: Keranjang, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == keranjang.user_id, User.role == "pembeli").first()
    if not user:
        raise HTTPException(status_code=404, message="Pembeli tidak ditemukan atau tidak terdaftar sebagai pembeli")

    barang = db.query(Barang).filter(Barang.id == keranjang.barang_id).first()
    if not barang:
        raise HTTPException(status_code=404, message="Barang tidak ditemukan")

    db.add(keranjang)
    db.commit()
    db.refresh(keranjang)
    return keranjang

@cihuyy.get("/keranjangs/", response_model=List[Keranjang])
def lihat_semua_keranjang(db: Session = Depends(get_db)):
    return db.query(Keranjang).all()

@cihuyy.get("/keranjangs/{keranjang_id}", response_model=Keranjang)
def lihat_keranjang(keranjang_id: UUID, db: Session = Depends(get_db)):
    keranjang = db.query(Keranjang).filter(Keranjang.id == keranjang_id).first()
    if not keranjang:
        raise HTTPException(status_code=404, message="Keranjang tidak ditemukan")
    return keranjang

@cihuyy.delete("/keranjangs/{keranjang_id}")
def hapus_keranjang(keranjang_id: UUID, db: Session = Depends(get_db)):
    keranjang = db.query(Keranjang).filter(Keranjang.id == keranjang_id).first()
    if not keranjang:
        raise HTTPException(status_code=404, message="Keranjang tidak ditemukan")
    db.delete(keranjang)
    db.commit()
    return {"message": "Keranjang berhasil dihapus"}




@cihuyy.post("/komentars/", response_model=Komentar)
def buat_komentar(komentar: Komentar, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == komentar.user_id).first()
    if not user:
        raise HTTPException(status_code=404, message="Pengguna tidak ditemukan")

    barang = db.query(Barang).filter(Barang.id == komentar.barang_id).first()
    if not barang:
        raise HTTPException(status_code=404, message="Barang tidak ditemukan")

    db.add(komentar)
    db.commit()
    db.refresh(komentar)
    return komentar

@cihuyy.get("/komentars/", response_model=List[Komentar])
def lihat_semua_komentar(db: Session = Depends(get_db)):
    return db.query(Komentar).all()

@cihuyy.get("/komentars/{komentar_id}", response_model=Komentar)
def lihat_komentar(komentar_id: UUID, db: Session = Depends(get_db)):
    komentar = db.query(Komentar).filter(Komentar.id == komentar_id).first()
    if not komentar:
        raise HTTPException(status_code=404, message="Komentar tidak ditemukan")
    return komentar

@cihuyy.delete("/komentars/{komentar_id}")
def hapus_komentar(komentar_id: UUID, db: Session = Depends(get_db)):
    komentar = db.query(Komentar).filter(Komentar.id == komentar_id).first()
    if not komentar:
        raise HTTPException(status_code=404, message="Komentar tidak ditemukan")
    db.delete(komentar)
    db.commit()
    return {"message": "Komentar berhasil dihapus"}

@cihuyy.put("/pesanans/{pesanan_id}", response_model=Pesanan)
def update_pesanan(pesanan_id: UUID, updated_pesanan: Pesanan, db: Session = Depends(get_db)):
    pesanan = db.query(Pesanan).filter(Pesanan.id == pesanan_id).first()
    if not pesanan:
        raise HTTPException(status_code=404, message="Pesanan tidak ditemukan")

    pesanan.pembeli_id = updated_pesanan.pembeli_id
    pesanan.barang_id = updated_pesanan.barang_id
    pesanan.jumlah = updated_pesanan.jumlah

    db.commit()
    db.refresh(pesanan)
    return pesanan


@cihuyy.put("/keranjangs/{keranjang_id}", response_model=Keranjang)
def update_keranjang(keranjang_id: UUID, updated_keranjang: Keranjang, db: Session = Depends(get_db)):
    keranjang = db.query(Keranjang).filter(Keranjang.id == keranjang_id).first()
    if not keranjang:
        raise HTTPException(status_code=404, message="Keranjang tidak ditemukan")

    keranjang.user_id = updated_keranjang.user_id
    keranjang.barang_id = updated_keranjang.barang_id
    keranjang.jumlah = updated_keranjang.jumlah

    db.commit()
    db.refresh(keranjang)
    return keranjang


@cihuyy.put("/komentars/{komentar_id}", response_model=Komentar)
def update_komentar(komentar_id: UUID, updated_komentar: Komentar, db: Session = Depends(get_db)):
    komentar = db.query(Komentar).filter(Komentar.id == komentar_id).first()
    if not komentar:
        raise HTTPException(status_code=404, message="Komentar tidak ditemukan")

    komentar.user_id = updated_komentar.user_id
    komentar.barang_id = updated_komentar.barang_id
    komentar.isi = updated_komentar.isi

    db.commit()
    db.refresh(komentar)
    return komentar


uvicorn.run(cihuyy, host="localhost", port=8000)