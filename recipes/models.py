
import base64
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, BLOB
from sqlalchemy.orm import sessionmaker, relationship


from recipes import config

engine = create_engine(config.DB_URL, echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)  # session class
# session = Session()  # session instance


class Recipes(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    ingredients = Column(String)
    photo = Column(BLOB)
    category_id = Column(Integer, ForeignKey('category.id'))
    steps = Column(String)

    category = relationship('Category', backref='recipes')

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'ingredients': self.ingredients,
            'photo': 'data:image/jpg;base64,{}'.format(base64.b64encode(self.photo).decode()),
            'category': self.category.category_name,
            'steps': self.steps
        }

    @classmethod
    def get_some(cls):
        results = []
        results += [recipes.as_dict() for recipes in Session().query(cls).limit(3)]
        return results

    @classmethod
    def get_by_category(cls, category):
        results = []
        results += [recipes.as_dict() for recipes in Session().query(cls).join(Category).filter(Category.category_name == category).all()]
        return results


    @classmethod
    def get_by_id(cls, id):
        result = Session().query(cls).filter(cls.id == id).first()
        return result.as_dict()

    @classmethod
    def get_favourites(cls, user_id):
        results = []
        results += [recipes.as_dict() for recipes in Session().query(cls).join(Favourite).filter(Favourite.user_id == user_id).all()]
        return results


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    category_name = Column(String)

    def as_dict(self):
        return {
            'id': self.id,
            'category_name': self.category_name
        }


    @classmethod
    def get_all(cls):
        results = []
        results += [category.as_dict() for category in Session().query(cls).all()]
        return results


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    mail = Column(String)
    password = Column(String)
    name = Column(String)


    def as_dict(self):
        return {
            'id': self.id,
            'login': self.mail,
            'name': self.name
        }

    @classmethod
    def find_by_mail_password(cls, mail, password):
        session = Session()
        user = session.query(cls).filter(
            cls.mail == mail,
            cls.password == password
        ).first()
        if user:
            return user.as_dict()
        else:
            return None

    @classmethod
    def add_new(cls, mail, password, name):
        session = Session()
        new_user = User(mail=mail, password=password, name=name)
        session.add(new_user)
        session.commit()


class Favourite(Base):
    __tablename__ = 'user_favourite'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    recipe_id = Column(Integer, ForeignKey('recipes.id'))

    user = relationship('User', backref='user_favourite')
    recipe = relationship('Recipes', backref='user_favourite')

    @classmethod
    def delete_by_id(cls, id, user_id):
        session = Session()
        session.query(cls).filter(cls.recipe_id == id, cls.user_id == user_id,).delete()
        session.commit()

    @classmethod
    def get_count_favourites(cls, user_id):
        session = Session()
        count = session.query(cls).filter(cls.user_id == user_id).count()
        return count

    @classmethod
    def add_by_id(cls, id, user_id):
        session = Session()
        new_recipe = Favourite(recipe_id=id, user_id=user_id)
        session.add(new_recipe)
        session.commit()
