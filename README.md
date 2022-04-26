<h1 align="center">Welcome to OSSAT (API) 💻</h1>
<p>
  <a href="https://www.gnu.org/licenses/gpl-3.0.en.html" target="_blank">
    <img alt="License: GNU GPLv3" src="https://img.shields.io/badge/License-GNU GPLv3-yellow.svg" />
  </a>
</p>

> Django GraphQL API for [OSSAT](https://github.com/tdherring/ossat-frontend). 
> 
> A Final Year Master's Project, developed for [King's College London](https://www.kcl.ac.uk/).

### 🏠 [Demo (Frontend Only)](https://ossat.io/)

## Configuration

These instructions assume you are going to use the default setup (MySQL, SMTP), but you may edit the code to amend the middleware accordingly if desired.

*Settings discussed here can all be found in* `core/settings.py`. 

1. A MySQL database called "ossat" setup on local machine with admin user: "ossat_admin".
   * *Note*: If you are hosting the database remotely, or want to change any of these details, change these in the `DATABASES` section.
2. Two environment variables configured:
   * `OSSAT_DB_PASS` which contains your database password.
   * `OSSAT_EMAIL_ADMIN_PASS` which contains your SMTP user password.
   * `SECRET_KEY` to secure signed data (Optional). 
4. `DEFAULT_FROM_EMAIL`, and all settings `EMAIL_<SETTING>` configured as appropriate. 
5. Configure `ALLOWED_HOSTS` and `CORS_ORIGIN_WHITELIST` to contain the URL and/or IP address of your frontend.
 
## Install

```sh
python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
```

## Usage

If running locally:

```sh
python manage.py runserver
```

*Or deploy to a cloud environment using your provider's instructions.*

## Author

👤 **Tom Herring**

* Github: [@tdherring](https://github.com/tdherring)
* LinkedIn: [@tomh99](https://linkedin.com/in/tomh99)

## 📝 License

Copyright © 2022 [Tom Herring](https://github.com/tdherring).<br />
This project is [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) licensed.
