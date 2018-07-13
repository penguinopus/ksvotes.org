from app.main import main
from flask import g, url_for, render_template, jsonify, request, redirect, session as http_session, abort, current_app
import time
from app.main.forms import *
from app.models import Registrant
from app import db
from uuid import UUID, uuid4
from app.decorators import InSession
from app.services import SessionManager
from app.services.steps import Step_0
from app.main.helpers import guess_locale

@main.route('/terms-of-service', methods=['GET'])
def terms():
    g.locale = guess_locale()
    return render_template('terms-of-service.html')

@main.route('/privacy-policy', methods=['GET'])
def privacy():
    g.locale = guess_locale()
    return render_template('privacy-policy.html')

#step 0 / 0x
@main.route('/', methods=["GET", "POST"])
@InSession
def index():
    registrant = g.get("registrant")
    form = FormStep0()
    if registrant:
        form = FormStep0(
            name_first = registrant.registration_value.get('name_first'),
            name_last = registrant.registration_value.get('name_last'),
            dob = registrant.registration_value.get('dob'),
            county = registrant.registration_value.get('county'),
            email = registrant.registration_value.get('email'),
            phone = registrant.registration_value.get('phone')
        )

    if request.method == "POST" and form.validate_on_submit():
        step = Step_0(form.data)
        if registrant:
            g.registrant.update(form.data)
        else:
            sid = UUID(http_session.get('session_id'), version=4)
            registrant = Registrant(
                county = form.data.get('county'),
                registration_value = form.data,
                session_id = sid,
                lang = g.lang_code,
            )
            db.session.add(registrant)

        step.run()
        registrant.reg_lookup_complete = step.reg_lookup_complete
        db.session.commit()

        http_session['reg_found'] = str(step.reg_found)

        session_manager = SessionManager(registrant, step)
        return redirect(session_manager.get_redirect_url())

    else:
        return render_template('index.html', form=form)

@main.route('/change-or-apply/', methods=["GET"])
@InSession
def change_or_apply():
    reg_found = http_session.get('reg_found', None)
    http_session['reg_found'] = None # do not persist
    return render_template('change-or-apply.html', reg_found=reg_found)

@main.route('/ref', methods=['POST'])
def referring_org():
    # we will accept whatever subset of step0 fields are provided.
    # we always start a new session, but we require a 'ref' code.
    if not request.values.get('ref'):
        return abort(404)

    sid = str(uuid4())
    http_session['session_id'] = sid
    registration = {
        'name_last': request.values.get('name_last', ''),
        'name_first': request.values.get('name_first', ''),
        'dob': request.values.get('dob', ''),
        'email': request.values.get('email', ''),
        'phone': request.values.get('phone', ''),
    }
    registrant = Registrant(
        session_id = sid,
        county = request.values.get('county', ''),
        ref = request.values['ref'],
        registration_value = registration
    )
    db.session.add(registrant)
    db.session.commit()
    return redirect('/')