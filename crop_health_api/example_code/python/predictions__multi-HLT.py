from httpx import Client

with Client() as client:
    # Get the multi-HLT model prediction for image cocoa.jpg
    # passed as a binary file in the request body
    response_multi_HLT = client.post(
        url="$api_url" + "/predictions/multi-HLT",
        data=open("cocoa.jpg", "rb").read(),
    )

    data_multi_HLT = response_multi_HLT.json()
    # Print the top 5 predictions
    print(data_multi_HLT)