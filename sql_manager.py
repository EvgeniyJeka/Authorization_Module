

class SqlManager(object):

    def get_users(self)-> set:
        return {"JustMe", "JustYou"}

    def save_jwt_key_time(self, key, time):
        return True

    def get_password_by_username(self, username):
        return hash("MyPassword")

    def get_data_by_token(self, token):
        return "tempKey", 1648743766.707471

    def get_allowed_actions_by_user(self, username):
        return [1, 2, 3]

# DB TABLE should contain the following rows: user ID, username, password (hashed),
# JWT generation key, JWT generation time

if __name__ == '__main__':
    a = '22 33 45'
    b = list(a.split(" "))
    print(b)
