from datetime import date
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_from_directory

from eventos.errors import (
    DatabaseError,
    DomainError,
    EventNotFound,
    RegistrationNotCancelable,
    RegistrationNotFound,
)
from eventos.service import EventService
from main import _service


WEB_DIRECTORY = Path(__file__).with_name("web")


def _event_payload(event) -> dict:
    return {
        "id": event.id_evento,
        "name": event.nome,
        "date": event.data.isoformat(),
        "location": event.local,
        "capacity": event.capacidade,
        "occupied": event.vagas_ocupadas,
        "available": event.vagas_disponiveis,
        "waiting": event.tamanho_fila,
        "status": event.status,
    }


def create_app(service: Optional[EventService] = None) -> Flask:
    app = Flask(__name__)
    app.config["EVENT_SERVICE"] = service or _service()

    @app.get("/")
    def index():
        return send_from_directory(WEB_DIRECTORY, "index.html")

    @app.get("/assets/<path:filename>")
    def assets(filename: str):
        return send_from_directory(WEB_DIRECTORY / "assets", filename)

    @app.get("/api/events")
    def list_events():
        event_date = None
        if request.args.get("date"):
            try:
                event_date = date.fromisoformat(request.args["date"])
            except ValueError:
                return jsonify(error="Use a data no formato AAAA-MM-DD."), 400
        events = app.config["EVENT_SERVICE"].list_events(
            name=request.args.get("name") or None,
            event_date=event_date,
            location=request.args.get("location") or None,
        )
        return jsonify([_event_payload(event) for event in events])

    @app.post("/api/events")
    def create_event():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Envie os dados do evento em formato JSON."), 400
        raw_date = data.get("date")
        if not isinstance(raw_date, str):
            return jsonify(error="Informe uma data válida no formato AAAA-MM-DD."), 400
        try:
            event_date = date.fromisoformat(raw_date)
        except ValueError:
            return jsonify(error="Informe uma data válida no formato AAAA-MM-DD."), 400
        event = app.config["EVENT_SERVICE"].create_event(
            data.get("name"),
            event_date,
            data.get("location"),
            data.get("capacity"),
        )
        return jsonify(_event_payload(event)), 201

    @app.post("/api/events/<int:event_id>/registrations")
    def register(event_id: int):
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Envie nome e e-mail em formato JSON."), 400
        registration = app.config["EVENT_SERVICE"].register(
            event_id,
            data.get("name"),
            data.get("email"),
        )
        return jsonify(
            {
                "id": registration.id_inscricao,
                "event_id": registration.id_evento,
                "status": registration.status,
            }
        ), 201

    @app.get("/api/registrations/<int:registration_id>")
    def get_registration(registration_id: int):
        registration = app.config["EVENT_SERVICE"].get_registration(registration_id)
        return jsonify(
            {
                "id": registration.id_inscricao,
                "event_id": registration.id_evento,
                "status": registration.status,
            }
        )

    @app.delete("/api/registrations/<int:registration_id>")
    def cancel_registration(registration_id: int):
        result = app.config["EVENT_SERVICE"].cancel_registration(registration_id)
        return jsonify(
            {
                "cancelled_id": result.cancelada.id_inscricao,
                "promoted_id": result.promovida.id_inscricao if result.promovida else None,
            }
        )

    @app.errorhandler(EventNotFound)
    @app.errorhandler(RegistrationNotFound)
    def not_found(error):
        return jsonify(error=str(error)), 404

    @app.errorhandler(RegistrationNotCancelable)
    @app.errorhandler(DomainError)
    def invalid_request(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(DatabaseError)
    def database_error(error):
        return jsonify(error=str(error)), 503

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
