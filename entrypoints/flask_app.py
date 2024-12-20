from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from domain import model 
from adapters import orm
from adapters import repository
from service_layer import services


orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
  print("Before")
  session = get_session()
  repo = repository.SqlAlchemyRepository(session)
  line = model.OrderLine(
    request.json["orderid"], request.json["sku"], request.json["qty"],
  )
  print("after")

  try: 
    batchref = services.allocate(line, repo, session)
  except (model.OutOfStock, services.InvalidSku) as e:
    return {"message": str(e)}, 400

  return {"batchref": batchref}, 201