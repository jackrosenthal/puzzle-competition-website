# -*- coding: utf-8 -*-
"""
Auth* related model.

This is where the models used by the authentication stack are defined.

It's perfectly fine to re-use this definition in the puzzlesweb application,
though.

"""
import os
import tg
import enum
from datetime import datetime
from hashlib import sha256
__all__ = ['User', 'Group', 'Permission']

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime, Enum
from sqlalchemy.orm import relation, synonym, relationship
from puzzlesweb.lib.mpapi_connector import auth
from puzzlesweb.model import DeclarativeBase, metadata, DBSession
import puzzlesweb.model.puzzlecomp

# This is the association table for the many-to-many relationship between
# groups and permissions.
group_permission_table = Table('tg_group_permission', metadata,
                               Column('group_id', Integer,
                                      ForeignKey('tg_group.group_id',
                                                 onupdate="CASCADE",
                                                 ondelete="CASCADE"),
                                      primary_key=True),
                               Column('permission_id', Integer,
                                      ForeignKey('tg_permission.permission_id',
                                                 onupdate="CASCADE",
                                                 ondelete="CASCADE"),
                                      primary_key=True))


# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships.
user_group_table = Table('tg_user_group', metadata,
                         Column('user_id', Integer,
                                ForeignKey('tg_user.user_id',
                                           onupdate="CASCADE",
                                           ondelete="CASCADE"),
                                primary_key=True),
                         Column('group_id', Integer,
                                ForeignKey('tg_group.group_id',
                                           onupdate="CASCADE",
                                           ondelete="CASCADE"),
                                primary_key=True))


class Group(DeclarativeBase):
    """
    Group definition

    Only the ``group_name`` column is required.

    """

    __tablename__ = 'tg_group'

    group_id = Column(Integer, autoincrement=True, primary_key=True)
    group_name = Column(Unicode(16), unique=True, nullable=False)
    display_name = Column(Unicode(255))
    created = Column(DateTime, default=datetime.now)
    users = relation('User', secondary=user_group_table, backref='groups')

    def __repr__(self):
        return '<Group: name=%s>' % repr(self.group_name)

    def __unicode__(self):
        return self.group_name

class PrivacySetting(enum.Enum):
    always = 0
    auth = 1
    admin = 2

class User(DeclarativeBase):
    """
    User definition.

    This is the user definition used by :mod:`repoze.who`, which requires at
    least the ``user_name`` column.

    """
    __tablename__ = 'tg_user'

    user_id = Column(Integer, autoincrement=True, primary_key=True)
    user_name = Column(Unicode(255), unique=True, nullable=False)
    display_name = Column(Unicode(255))
    created = Column(DateTime, default=datetime.now)
    puzzles = relationship('puzzlesweb.model.puzzlecomp.Puzzle', back_populates='author')
    submissions = relationship('puzzlesweb.model.puzzlecomp.Submission', back_populates='user')
    privacy = Column(Enum(PrivacySetting), nullable=False, default=PrivacySetting.always)

    def __repr__(self):
        return '<User: name=%s, display=%s>' % (
            repr(self.user_name),
            repr(self.display_name)
        )

    def __str__(self):
        return self.display_name or self.user_name

    @property
    def permissions(self):
        """Return a set with all permissions granted to the user."""
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms

    @classmethod
    def by_user_name(cls, username):
        """Return the user object whose user name is ``username``."""
        return DBSession.query(cls).filter_by(user_name=username).first()

    def validate_password(self, password):
        """
        Check the password against existing credentials.

        :param password: the password that was provided by the user to
            try and authenticate. This is the clear text version that we will
            need to match against the hashed one in the database.
        :type password: unicode object.
        :return: Whether the password is valid.
        :rtype: bool

        """
        return auth(self.user_name, password)

class Permission(DeclarativeBase):
    """
    Permission definition.

    Only the ``permission_name`` column is required.

    """

    __tablename__ = 'tg_permission'

    permission_id = Column(Integer, autoincrement=True, primary_key=True)
    permission_name = Column(Unicode(63), unique=True, nullable=False)
    description = Column(Unicode(255))

    groups = relation(Group, secondary=group_permission_table,
                      backref='permissions')

    def __repr__(self):
        return '<Permission: name=%s>' % repr(self.permission_name)

    def __unicode__(self):
        return self.permission_name
