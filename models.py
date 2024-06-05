from collections import UserList
from csv import unregister_dialect
from dataclasses import fields
from flask_sqlalchemy import SQLAlchemy
from datetime import  date
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError, validates, RAISE, fields, pprint
from pyparsing import dblSlashComment
from sqlalchemy import PrimaryKeyConstraint, false



db = SQLAlchemy()
ma = Marshmallow()


class Book(db.Model):
    __tablename__ = 'books'
    
    id              = db.Column(db.Integer,     primary_key=True, unique=True)
    author_id       = db.Column(db.Integer,     db.ForeignKey('authors.id'), nullable=True)
    price           = db.Column(db.Integer,     default=25)
    copies_sold     = db.Column(db.Integer,     default=0)
    date_published  = db.Column(db.Date(),      nullable=True)
    genre           = db.Column(db.String(100), nullable=True)
    isbn            = db.Column(db.String(18),  unique=True)
    description     = db.Column(db.String(250), nullable=True)
    title           = db.Column(db.String(100), nullable=True)
    publisher       = db.Column(db.String(100), nullable=True)
    wishlists       = db.Column(db.Integer,     db.ForeignKey('wishlists.id'), nullable=True)
    shoppingCarts   = db.Column(db.Integer,     db.ForeignKey('shoppingCarts.id'), nullable=True)
    ratings         = db.relationship('Rating', backref='book')
    comments        = db.relationship('Comment', backref='book')

    # helper function to format date for as_dict function
    def set_value(self, name):
        val = getattr(self, name)
        if type(val) is date:
            return val.isoformat()
        return val

    def as_dict(self):
        return {c.name: self.set_value(c.name) for c in self.__table__.columns if c.name not in ['wishlists', 'shoppingCarts']}

    def __repr__(self) -> str:
        return f"{self.title} by {str.title(self.author.last_name)}, {str.title(self.author.first_name)} (ISBN: {self.isbn})"
    
class Author(db.Model):
    __tablename__ = 'authors'
    
    id              = db.Column(db.Integer, primary_key=True, unique=True)
    first_name      = db.Column(db.String(50), nullable=True)
    last_name       = db.Column(db.String(50), nullable=True)
    publisher       = db.Column(db.String(50), nullable=True)
    bio             = db.Column(db.String(500), nullable=True)
    books           = db.relationship('Book', backref='author')
    

    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self):
        return f"{self.first_name} {self.last_name}. Bio: {self.bio}"


class Wishlist(db.Model):
    __tablename__ = 'wishlists'

    id                  = db.Column(db.Integer, primary_key=True, unique=True)
    user_id             = db.Column(db.Integer,db.ForeignKey('users.id'), nullable=True)
    books               = db.relationship('Book', backref='wishlist')
    
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self) -> str:
            return f"id: {self.id}, user_id: {self.user_id}"

class ShoppingCart(db.Model):
    __tablename__ = 'shoppingCarts'
    
    id                  = db.Column(db.Integer, primary_key=True, unique=True)
    user_id             = db.Column(db.Integer,db.ForeignKey('users.id'), nullable=True)
    books               = db.relationship('Book', backref='shoppingcart')

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self) -> str:
        return f"id: {self.id}, user_id: {self.user_id}"
    
class User(db.Model):
    __tablename__ = 'users'
    
    id                  = db.Column(db.Integer, primary_key=True, unique=True)
    username            = db.Column(db.String(50), nullable=True)
    first_name          = db.Column(db.String(50), nullable=True)
    last_name           = db.Column(db.String(50), nullable=True)
    isAdmin             = db.Column(db.Boolean, default=False)
    wishlist            = db.relationship('Wishlist', backref='user', uselist=False)
    shoppingCart        = db.relationship('ShoppingCart', backref='user', uselist=False)
    comments            = db.relationship('Comment', backref='user')
    ratings             = db.relationship('Rating', backref='user')
    # emailAddress        = db.Column(db.String(50), nullable=True)
    homeAddress         = db.Column(db.String(100), nullable=True)
    password            = db.Column(db.String(50), nullable=True)
    credit_card          = db.relationship('CreditCard', backref='user')




    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    

    def __repr__(self):
        return f"{self.username}, isAdmin: {self.isAdmin}"


class CreditCard(db.Model):
    __tablename__ = 'creditCards'
    
    id                 = db.Column(db.Integer, primary_key=True, unique=True)
    user_id            = db.Column(db.Integer,db.ForeignKey('users.id'), nullable=True)
    credit_card         = db.Column(db.String(50), nullable=True) 

class Rating(db.Model):
    __tablename__ ='ratings'
    
    id              = db.Column(db.Integer, primary_key=True, unique=True)
    book_id         = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating          = db.Column(db.Integer)
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
class Comment(db.Model):
    __tablename__ = 'comments'
    
    id              = db.Column(db.Integer, primary_key=True, unique=True)
    book_id         = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_text    = db.Column(db.String(200))
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


    def __repr__(self):
        return f"id:{self.id}, book_id:{self.book_id}, user_id:{self.user_id}, comment_text:{self.comment_text}"


"""
    the class below are Marshmallow schema classes for the sqlalchemy classes above.
    i use them for validation but can also be used for (de)serializing the ORM objects
"""

class BookSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Book
        include_relationships = False
        include_fk = True
        dateformat = '%Y-%m-%d'
        unknown = RAISE
    
    @validates('isbn')
    def validate_isbn(self, val):
        isbn_cleaned = val.translate({ord("-"):None, ord(" "): None }) # remove "-" and spaces from isbn string
        if not isbn_cleaned.isnumeric():
            raise ValidationError(f"Invalid ISBN: {val}. must be a string containing ONLY numbers, '-' or a spaces ")
    
    # optional fields to create author if they are provided when creating book
    first_name = fields.String()
    last_name = fields.String()



class AuthorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Author
        include_relationships = True
        include_fk = True

    books = fields.Nested(BookSchema, many=True)

class UserSchema(ma.SQLAlchemyAutoSchema):
    
    class Meta:
        model = User
        include_relationships = True
        include_fk = True
    
    wishlist = fields.Nested(lambda: WishlistSchema(only=('books',)))
    shoppingCart = fields.Nested(lambda: ShoppingCartSchema(only=('books',)))



    @validates('creditCard')
    def validate_creditCard(self, val):
        creditCard_cleaned = val.translate({ord("-"):None, ord(" "): None }) # remove "-" and spaces from creditCard string
        if not creditCard_cleaned.isnumeric():
            raise ValidationError(f"Invalid Credit Card: {val}. must be a string containing ONLY numbers, '-' or a spaces ")


class CreditCardSchema(ma.SQLAlchemyAutoSchema):
    
    class Meta:
        model = CreditCard
        include_relationships = True
        include_fk = True
        unknown = RAISE
    
    user = fields.Nested('UserSchema', only=('username',))


class ShoppingCartSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ShoppingCart
        include_relationships = True
        include_fk = True
    
    user = fields.Nested(UserSchema)
    books = fields.Nested(BookSchema)

class WishlistSchema(ma.SQLAlchemyAutoSchema):
    
    class Meta:
        model = Wishlist
        include_relationship = True
        include_fk = True
    
    user = fields.Nested(UserSchema)
    books = fields.Nested(BookSchema)


class RatingSchema(ma.SQLAlchemyAutoSchema):
    
    class Meta:
        model = Rating
        include_relationships = True
        include_fk = True

    book = fields.Nested(BookSchema)
    user = fields.Nested(UserSchema)


class CommentSchema(ma.SQLAlchemyAutoSchema):
    
    class Meta:
        model = Comment
        include_relationships = True
        include_fk = True

    book = fields.Nested(BookSchema)
    user = fields.Nested(UserSchema)

