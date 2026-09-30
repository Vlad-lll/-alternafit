from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Usuário do sistema. Por enquanto é idêntico ao usuário padrão do Django
    (username, e-mail, senha, is_staff...). Existe desde o início do projeto
    para que campos novos possam ser adicionados no futuro sem precisar
    recriar o banco.
    """
