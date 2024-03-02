import os
from flask import Flask, request
from flask import Blueprint
from SpeakerDiarization.Speaker_Diarization import SpeakerDiarization

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/diarization', methods=['POST'])
   #if 'audio' not in request.files:
       #return jsonify({'error': 'No audio file provided'}), 400
def diarization():
    try:
        audio_file = request.files['audio']
        account_id = request.form['accountId']
        timestamp = request.form['timeStamp']
        require_summary = request.form['summaryReq']

        if audio_file == '':
            return jsonify({'error': 'Failed to retrive audio'}), 400

        if account_id == '':
            return jsonify({'error': 'Account information missing'}), 400

        os.makedirs('audioFiles/'+account_id, exist_ok=True)

        file_path = os.path.join('audioFiles/'+account_id, account_id+'_'+timestamp+_+require_summary+'.wav')
        audio_file.save(file_path)

        return 'Hello World'

    except Exception as e:
        print(f"Error processing upload: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500