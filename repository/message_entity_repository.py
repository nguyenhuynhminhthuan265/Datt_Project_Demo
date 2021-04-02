from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models.entity.models import MessageEntity

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_message_entity(db: Session, message_entity: MessageEntity ):
    # db_message_entity = models.MessageEntity(message=message_entity_create.message,
    #                                          id_user_sender=message_entity_create.id_user_sender,
    #                                          id_user_receiver=message_entity_create.id_user_receiver)
    db.add(message_entity)
    db.commit()
    db.refresh(message_entity)
    return message_entity
