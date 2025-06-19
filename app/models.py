from app import db, bcrypt, login_manager
from flask_login import UserMixin
from sqlalchemy import func

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False)
    statements = db.relationship('Statement', backref='user', lazy=True)

    @property
    def password_hash(self):
        return self.password_hash
    
    @password_hash.setter
    def password_hash(self, plain_password):
        self.password = bcrypt.generate_password_hash(plain_password).decode('utf-8')

    def check_password(self, attempted_password):
        return bcrypt.check_password_hash(self.password, attempted_password)
    
class Statement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=func.datetime('now', 'localtime'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_statement_user'), nullable=False)