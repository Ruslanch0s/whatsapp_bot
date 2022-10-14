from whatsaap import Whatsapp


def main():
    TG_TOKEN = 'your_tg_token'
    TG_ADMIN_ID = 1234

    # executable_path = str(Path(cfg.root_path, 'drivers', 'chromedriver-106-m1'))
    # executable_path = ChromeDriverManager().install()
    whats_app = Whatsapp(telegram_bot_token=TG_TOKEN,
                         telegram_admin_id=TG_ADMIN_ID)

    whats_app.run()
    whats_app.send_message(user_name='Name', text='Hello!')
    whats_app.finish()


if __name__ == '__main__':
    main()
