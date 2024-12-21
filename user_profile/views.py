import csv
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
from .models import CustomUser
from django.db import transaction


def file_row_generator(file_obj):
    """
    Generator function to yield each decoded line from a file object.
    Args:
        file_obj (CSV file): Each line will read from the CSV file.

    Yields:
        str: A single decoded and stripped line from the file.
        
    Raises:
        UnicodeDecodeError: If the line cannot be decoded using 'utf-8'.
    """
    for line in file_obj:
        decoded_line = line.decode('utf-8').strip()
        if decoded_line: 
            yield decoded_line
            

@api_view(['POST'])
def upload_user_details(request):
    """
    Endpoint to upload user details from a CSV file and store them in the database.
    
    The file format should be CSV, and duplicates based on the 'email' field will be rejected.
    Validated records will be saved in the CustomUser model in batches of up to 100 records.

    Args:
        request (request): The HTTP request object containing the uploaded CSV file.

    Returns:
        Response: A response containing the status of the file processing, 
                  the number of successfully saved records, the number of 
                  rejected records, and any errors encountered.
    Raises:
        HTTP_400_BAD_REQUEST: If no file is uploaded or the file is not a CSV.
        HTTP_500_INTERNAL_SERVER_ERROR: If an exception occurs during processing.
        
    """
    BATCH_SIZE = 100
    if request.method == "POST":
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        if not file.name.endswith('.csv'):
            return Response({"error": "File must have a .csv extension."}, status=status.HTTP_400_BAD_REQUEST)

        saved_records = 0
        rejected_records = 0
        errors = []
        user_objects = []
        seen_emails = set()

        try:
            csv_reader = csv.DictReader(file_row_generator(file))

            for row_num, row in enumerate(csv_reader, start=1):
                row_num +=1
                email = row.get('email')
                # Check for duplicate emails in the CSV
                if email in seen_emails:
                    errors.append({
                        "row": row_num,
                        "error": f"Duplicate email in file: {email}"
                    })
                    rejected_records += 1
                    continue
                seen_emails.add(email)
                
                # Serialize data for user creation
                serialized_data = UserSerializer(data=row)
                if serialized_data.is_valid():
                    user = CustomUser(**serialized_data.validated_data)
                    user_objects.append(user)
                    saved_records += 1
                    
                    # Batch insert into database after reaching the batch size
                    if len(user_objects) >= BATCH_SIZE:
                        with transaction.atomic():
                            CustomUser.objects.bulk_create(user_objects)
                        user_objects.clear()
                else:
                    errors.append({"row": row_num, "error": serialized_data.errors})
                    rejected_records += 1
                    
            # process remaining user objects to the database
            if user_objects:
                with transaction.atomic():
                    CustomUser.objects.bulk_create(user_objects)
            
            # Return success response with details
            return Response({
                "message": "File processed successfully.",
                "saved_records": saved_records,
                "rejected_records": rejected_records,
                "errors": errors
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error1": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
