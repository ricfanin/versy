import glob
import os

import cv2
import numpy as np

CHESSBOARD_SIZE = (9, 6)  # Numero di angoli INTERNI (colonne, righe)
SQUARE_SIZE = 18  # Dimensione del quadrato in mm
NUM_IMAGES = 20  # Numero di immagini da catturare


# fase 1 dove catturo immagini
def capture_calibration_images():

    if not os.path.exists("calibration_images"):
        os.makedirs("calibration_images")

    print(f"Obiettivo: catturare {NUM_IMAGES} immagini")
    print("- Premi SPAZIO quando la scacchiera è rilevata (vedrai i punti verdi)")
    print("- Premi ESC per uscire")

    img_counter = 0
    cap = cv2.VideoCapture(0)

    while img_counter < NUM_IMAGES:
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Cerca gli angoli della scacchiera
        ret_chess, corners = cv2.findChessboardCorners(
            gray,
            CHESSBOARD_SIZE,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE,
        )
        # Visualizza scacchiera
        display_frame = frame.copy()
        if ret_chess:
            # Disegna gli angoli trovati
            cv2.drawChessboardCorners(
                display_frame, CHESSBOARD_SIZE, corners, ret_chess
            )
            cv2.putText(
                display_frame,
                "SCACCHIERA RILEVATA - Dai movate premi SPAZIO",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
        else:
            cv2.putText(
                display_frame,
                "Scacchiera non rilevata",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

        # Mostra contatore
        cv2.putText(
            display_frame,
            f"Immagini: {img_counter}/{NUM_IMAGES}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        cv2.imshow("Calibrazione Camera", display_frame)

        key = cv2.waitKey(1) & 0xFF

        # SPAZIO per catturare
        if key == ord(" ") and ret_chess:
            img_name = f"calibration_images/calib_{img_counter:02d}.jpg"
            cv2.imwrite(img_name, frame)
            print(f"Immagine {img_counter + 1}/{NUM_IMAGES} salvata: {img_name}")
            img_counter += 1

        # ESC per uscire
        elif key == 27:
            print("Uscita anticipata")
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n✓ Cattura completata: {img_counter} immagini salvate")
    return True


# fase 2 di calibrazione usando le immagini salvate
def calibrate_camera():
    print("\n=== CALIBRAZIONE IN CORSO ===\n")
    # Prepara i punti 3D della scacchiera nel mondo reale
    objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0 : CHESSBOARD_SIZE[0], 0 : CHESSBOARD_SIZE[1]].T.reshape(
        -1, 2
    )
    objp *= SQUARE_SIZE
    # Array per memorizzare i punti
    objpoints = []  # Punti 3D nel mondo reale
    imgpoints = []  # Punti 2D nell'immagine

    # Carica tutte le immagini
    images = glob.glob("calibration_images/*.jpg")

    if len(images) == 0:
        print("Errore: nessuna immagine trovata in calibration_images/")
        return None

    print(f"Elaborazione di {len(images)} immagini... ")
    valid_images = 0
    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE, None)
        if ret:
            # Raffina la posizione degli angoli
            corners_refined = cv2.cornerSubPix(
                gray,
                corners,
                (11, 11),
                (-1, -1),
                criteria=(
                    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                    30,
                    0.001,
                ),
            )
            objpoints.append(objp)
            imgpoints.append(corners_refined)
            valid_images += 1
            print(f"Valida {fname}")
        else:
            print(f"{fname} - scacchiera non rilevata")

    print(f"\n{valid_images}/{len(images)} immagini valide per la calibrazione")
    if valid_images < 10:
        print("Errore: troppe poche immagini valide (minimo 10)")
        return None

    # Esegui la calibrazione
    img_shape = gray.shape[::-1]
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, img_shape, None, None
    )

    if not ret:
        print("Errore durante la calibrazione")
        return None

    # Calcola l'errore di riproiezione
    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(
            objpoints[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs
        )
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        mean_error += error

    mean_error /= len(objpoints)

    print("\n=== RISULTATI CALIBRAZIONE ===")
    print(f"\nErrore medio di riproiezione: {mean_error:.3f} pixel")
    if mean_error < 0.5:
        print("Calibrazione eccellente!")
    elif mean_error < 1.0:
        print("Calibrazione buona")
    else:
        print("Calibrazione accettabile (considera di rifare con più immagini)")

    print("\n--- MATRICE INTRINSECA (Camera Matrix) ---")
    print(camera_matrix)

    print("\n--- COEFFICIENTI DI DISTORSIONE ---")
    print(dist_coeffs)

    np.savez(
        "camera_calibration.npz",
        camera_matrix=camera_matrix,
        dist_coeffs=dist_coeffs,
        error=mean_error,
    )

    print("\n Parametri salvati in 'camera_calibration.npz'")

    return camera_matrix, dist_coeffs


if __name__ == "__main__":
    print("=" * 60)
    print("CALIBRAZIONE CAMERA PER ARUCO POSE ESTIMATION")
    print("=" * 60)

    while True:
        print("\nMENU:")
        print("1. Cattura immagini dalla webcam")
        print("2. Esegui calibrazione")
        print("0. Esci")
        choice = input("\nScegli: ")
        if choice == "1":
            capture_calibration_images()
        elif choice == "2":
            calibrate_camera()
        elif choice == "0":
            print("Ciao!")
            break
        else:
            print("Scelta non valida")
