from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Categories, Base, Items, User

#create engine and create database session.
engine = create_engine('sqlite:///catalogapp.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#Add data to datbase session. 
#Add game categories, items, and  descriptions.

game1 = Categories(name="Soccer")

session.add(game1)
session.commit()

Item2 = Items(user_id=1, name="Ball", description="Nike or Addidas original Soccer ball.",
              categories=game1)

session.add(Item2)
session.commit()


game2 = Categories(name="Basketball")

session.add(game2)
session.commit()

Item1 = Items(user_id=1, name="Ball", description="New nike Basketball.",
              categories=game2)

session.add(Item1)
session.commit()


game1 = Categories(name="Baseball")

session.add(game1)
session.commit()

Item2 = Items(user_id=1, name="Ball", description="Original white color Baseball ball.",
              categories=game1)

session.add(Item2)
session.commit()

Item3 = Items(user_id=1, name="Bat", description="Nice adult size Baseball bat.",
              categories=game1)

session.add(Item3)
session.commit()


game2 = Categories(name="Frisbee")

session.add(game2)
session.commit()

Item1 = Items(user_id=1, name="Disk", description="Blue color Frisbee disk.",
              categories=game2)

session.add(Item1)
session.commit()


game1 = Categories(name="Snowbording")

session.add(game1)
session.commit()

Item2 = Items(user_id=1, name="Bord", description="Good quality Snowbording bord with nice design on it.",
              categories=game1)

session.add(Item2)
session.commit()


game2 = Categories(name="Rock Climbing")

session.add(game2)
session.commit()

Item1 = Items(user_id=1, name="Rope", description="White color unbreakable 100ft long rope.",
              categories=game2)

session.add(Item1)
session.commit()


game1 = Categories(name="Cricket")

session.add(game1)
session.commit()

Item2 = Items(user_id=1, name="Ball", description="Red color leather cricket ball.",
              categories=game1)

session.add(Item2)
session.commit()

Item3 = Items(user_id=1, name="Bat", description="Nike regular adult size cricket bat.",
              categories=game1)

session.add(Item3)
session.commit()


game2 = Categories(name="Hockey")

session.add(game2)
session.commit()

Item1 = Items(user_id=1, name="Stick", description="Regular size, good quality Hockey stick.",
              categories=game2)

session.add(Item1)
session.commit()

print "added all items!"