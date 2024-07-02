from httpx import Client

with Client() as client:
    # Get the single-HLT model prediction for image cocoa.jpg
    # passed as a binary file in the request body
    response_single_HLT = client.post(
        url="$api_url" + "/predictions/single-HLT",
        data=open("cocoa.jpg", "rb").read(),
    )

    data_single_HLT = response_single_HLT.json()
    # Print the preciteion for the CBSD class
    print(data_single_HLT["CBSD"])
