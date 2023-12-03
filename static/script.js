async function uploadPDF() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (file) {
        const formData = new FormData();
        formData.append('pdf', file);

        try {
            const response = await fetch('http://127.0.0.1:8000/upload', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                alert('PDF uploaded successfully!');
            } else {
                alert('Failed to upload PDF.');
            }
        } catch (error) {
            console.error('Error uploading PDF:', error);
        }
    } else {
        alert('Please select a PDF file.');
    }
}

async function askQuestion() {
    console.log('askQuestion function called');
    const questionInput = document.getElementById('questionInput');
    const question = questionInput.value;
    if (question) {
        try {
            console.log('Sending request...');
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question }),
            });

            console.log('Full Response:', response);

            if (response.ok) {
                const data = await response.json();
                console.log('Data:', data);

                const responseText = data.response;
                console.log('Response Text:', responseText);

                // Display the response on the frontend
                const responseDisplay = document.getElementById('responseDisplay');
                responseDisplay.innerText = responseText;
            } else {
                console.error('Failed to get a valid response.');
            }
        } catch (error) {
            console.error('Error asking the question:', error);
        }
    } else {
        alert('Please enter a question.');
    }
}

