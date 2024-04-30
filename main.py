from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

from pydantic import BaseModel, Field
from uuid import uuid4, UUID
from typing import Optional

from auth import create_token, validate_token
from sqlalchemy.orm import Session
from config.database import SessionLocal, engine, Base, get_db
from models.user import User as UserModel


app = FastAPI(title="FastAPI Auth service", version="0.0.1")

Base.metadata.create_all(bind=engine)

class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request, db:Session = Depends(get_db)): 
        auth = await super().__call__(request)
        data = validate_token(auth.credentials)
        if data:
                email = data.get('email')
                user = db.query(User).filter(User.email == email).first()
                if not user:
                    raise HTTPException(status_code=403, detail="Usuario no encontrado")
                return user
        else:
            raise HTTPException(status_code=403, detail="Invalid auth credentials")    
        
        
class User(BaseModel):
    username: str 
    password: str
    email: str

class User_creation(User):
    id: Optional[UUID] = Field(default_factory=uuid4, alias="_id")

users = []

@app.get('/')
def hello_world():
    return JSONResponse(content={"message": "Hello, World!"})

@app.post('/signup/', tags=["Auth"])
def signup(new_user: User, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == new_user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = new_user.password  # Aquí deberías agregar hashing de contraseña
    db_user = UserModel(username=new_user.username, password=hashed_password, email=new_user.email)
    db.add(db_user)
    db.commit()
    return JSONResponse(status_code=201, content={"message": "User created successfully!"})

@app.post('/login/',tags=["Auth"])
def login(inputUser: User):
    for user in users:
        if user.username == inputUser.username and user.password == inputUser.password:
            token: str = create_token(User(**user.dict()).dict())
            return JSONResponse(status_code=200, content=token)
    
    return JSONResponse(status_code=404 ,content={"message": "Invalid credentials!"})
