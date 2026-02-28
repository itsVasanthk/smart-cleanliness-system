from deepface import DeepFace

try:
    result = DeepFace.verify(
        img1_path="id_sample.jpg",
        img2_path="selfie_sample.jpg",
        enforce_detection=False
    )

    print("\nVerification Result:")
    print(result)

except Exception as e:
    print("Error occurred:", str(e))