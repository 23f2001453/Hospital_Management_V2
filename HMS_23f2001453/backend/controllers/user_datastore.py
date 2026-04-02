from flask_security import SQLAlchemyUserDatastore # type: ignore
from controllers.models import User, Role
from controllers.database import db    

user_datastore = SQLAlchemyUserDatastore(db, User, Role)

