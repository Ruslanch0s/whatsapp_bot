from whatsaap import Whatsapp


def main():
    TG_TOKEN = '5629704642:AAFpxYQeZ0KSnMcx7cC-xZ6to0HNkvnkdNM'
    TG_ADMIN_ID = 364294246

    # executable_path = str(Path(cfg.root_path, 'drivers', 'chromedriver-106-m1'))
    # executable_path = ChromeDriverManager().install()
    whats_app = Whatsapp(telegram_bot_token=TG_TOKEN,
                         telegram_admin_id=TG_ADMIN_ID)

    whats_app.run()
    whats_app.send_message(user_name='Name', text='Hello!')
    whats_app.finish()


if __name__ == '__main__':
    main()
