from flask import Flask, request, jsonify, send_from_directory
import zipfile
import time
import os

csv_dir = "/home/pi/logs"

def get_sessions():
    """
    Retrieves all sessions.
    """
    sessions = []
    for session in os.listdir(csv_dir):
        session_path = os.path.join(csv_dir, session)
        if os.path.isdir(session_path):
            sessions.append(session)
    return jsonify({"status": "success", "data": sessions}), 200

def delete_sessions():
    """
    Deletes all sessions.
    """
    try:
        for session in os.listdir(csv_dir):
            session_path = os.path.join(csv_dir, session)
            if os.path.isdir(session_path):
                for root, dirs, files in os.walk(session_path, topdown=False):
                    for file in files:
                        os.remove(os.path.join(root, file))
                    for dir in dirs:
                        os.rmdir(os.path.join(root, dir))
                os.rmdir(session_path)
        return jsonify({"status": "success", "message": "Deleted all sessions."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def export_and_zip_csv(folder_path, output_dir="/home/pi"):
    """
    Exports logs as a zip file by compressing all CSV files in the specified folder.

    Args:
        folder_path (str): Path to the folder containing CSV files.
        output_dir (str): Directory where the ZIP file will be saved.

    Returns:
        str: Path to the generated ZIP file.

    Raises:
        FileNotFoundError: If the folder does not exist.
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder {folder_path} does not exist.")

    timestamp = time.strftime('%Y%m%d_%H%M%S')
    zip_file = os.path.join(output_dir, f"logs_{timestamp}.zip")

    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".csv"):
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, folder_path)  # Zachowanie struktury folderów
                    zipf.write(full_path, arcname=arcname)

    return zip_file

def export_log():
    """
    Exports logs from the specified folder as a zip file.
    The folder path is provided as a query parameter 'folder'.
    """
    folder_path = f"/home/pi/logs/{request.args.get('folder')}"
    if not folder_path:
        return jsonify({"status": "failed", "message": "Folder path is required."}), 400

    try:
        zip_file = export_and_zip_csv(folder_path)
        directory = os.path.dirname(zip_file)  # Katalog, w którym znajduje się plik ZIP
        filename = os.path.basename(zip_file)  # Nazwa pliku ZIP
        return send_from_directory(directory=directory, path=filename, as_attachment=True)
    except FileNotFoundError as e:
        return jsonify({"status": "failed", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "failed", "message": "An error occurred.", "details": str(e)}), 500
        