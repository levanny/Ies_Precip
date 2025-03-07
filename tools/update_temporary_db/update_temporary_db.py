import requests
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.models import DivPositions
from src import create_app
# from src.config import TestConfig

def modify_station_details(station_details):
    for station_detail in station_details:

        # შევამოწმოთ უნდა თუ არა მონაცემის წამოღება
        if station_detail.stations.fetch_status != True:
            station_detail.first_div_height = 0.00
            station_detail.precip_rate = "xx:xx"
            station_detail.precip_accum = "xx:xx"
            station_detail.save()
            continue

         # http მოთხოვნას აგზავნის api-ზე რადგან წამოიღოს მონაცები
        response = requests.get(station_detail.stations.api)

        if response.status_code != 200:
             # თუ სადგურს ვერ დაუკავშირდა (გათიშუალია სადგური ან კავშირი ვერ შედგა) გაუწერს default მნიშვნელობებს და განაახლებს ბაზას
            logging.debug(f'დაკავშირება ვერ მოხერხდა {station_detail.stations.station_name} სადგურზე!')

            station_detail.first_div_height = 0.00
            station_detail.precip_rate = "--:--"
            station_detail.precip_accum = "--:--"
            station_detail.save()
            continue
        # სადგურთან კავშირის შემთხვევაში
        data = response.json()
        # მონაცემების ცვლადებში შენახვა და შემდგომ მათი ბაზაში განახლება
        try:
            precip_rate = data['observations'][0]['metric']['precipRate']
            precip_accum = data['observations'][0]['metric']['precipTotal']
            precip_rate = "{:.2f}".format(precip_rate)
            precip_accum = float(precip_accum)
        except:
            logging.debug(f"json დან მონაცემების ამოღების დროს მოხდა შეცდომა {station_detail.stations.station_name}")
            continue

        if precip_accum == 0.0:
            top_bottom = station_detail.static_px
            first_div_height = 0.00
        else:
            top_bottom = station_detail.static_px - precip_accum
            first_div_height = precip_accum

        station_detail.first_div_height = first_div_height
        station_detail.top_bottom = top_bottom
        station_detail.precip_accum = f'{precip_accum:.2f}'
        station_detail.precip_rate = precip_rate

        station_detail.save()

        logging.debug(f'მონაცემი წარმატებით დაემატა {station_detail.stations.station_name}')


def update_temporary_db():
    app = create_app()
    # app = create_app(TestConfig)
    with app.app_context():
        try:
            station_details = DivPositions.query.all()
            modify_station_details(station_details)
        except Exception as e:
            logging.critical(f"სკრიპტის შესრულების დროს შეცდომა: {e}")

if __name__ == "__main__":
    update_temporary_db()