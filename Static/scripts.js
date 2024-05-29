document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.getElementById('flash-messages');
    if (flashMessages) {
        setTimeout(() => {
            flashMessages.style.display = 'none';
        }, 5000);
    }

    const createPage = document.getElementById('create-assessment-page');
    const editPage = document.getElementById('edit-assessment-page');

    document.body.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('delete-question')) {
            if (confirm('Are you sure you want to delete this question?')) {
                e.target.parentNode.remove(); // Remove the question from the DOM
            }
        }
    });

    if (createPage) {
        // Code specific to Create Assessment page
    }

    if (editPage) {
        document.body.addEventListener('click', function(e) {
            if (e.target && e.target.classList.contains('delete-question')) {
                const questionBlock = e.target.closest('.question-block');
                const questionIdInput = questionBlock.querySelector('input[type="hidden"]');
                if (questionIdInput && questionIdInput.value && confirm('Are you sure you want to delete this question?')) {
                    const deletedQuestionsInput = document.getElementById('deleted-questions');
                    if (deletedQuestionsInput.value) {
                        deletedQuestionsInput.value += `,${questionIdInput.value}`;
                    } else {
                        deletedQuestionsInput.value = questionIdInput.value;
                    }
                    questionBlock.remove();  // This removes the question from the DOM
                }
            }
        });
    }

    const mcButton = document.getElementById('add-mc-question');
    const textButton = document.getElementById('add-text-question');
    const form = document.getElementById('assessment-form');

    // Function to add multiple-choice question block
    function addMultipleChoiceQuestion() {
        var container = document.getElementById('questions-container');
        var mcQuestionDiv = document.createElement('div');
        mcQuestionDiv.innerHTML = `
            <label for="mc-question-${questionCounter}"><strong>Question ${questionCounter}: </strong></label>
            <textarea id="mc-question-${questionCounter}" name="mc_question_${questionCounter}" placeholder="Enter the question"></textarea><br><br>

            <label for="mc-correct-answer-${questionCounter}">Correct Answer:</label>
            <textarea id="mc-correct-answer-${questionCounter}" name="mc_correct_answer_${questionCounter}" placeholder="Enter the correct answer"></textarea><br>

            <label for="mc-incorrect-answer1-${questionCounter}">Incorrect Answer 1:</label>
            <textarea id="mc-incorrect-answer1-${questionCounter}" name="mc_incorrect_answer1_${questionCounter}" placeholder="Enter incorrect answer 1"></textarea><br>

            <label for="mc-incorrect-answer2-${questionCounter}">Incorrect Answer 2:</label>
            <textarea id="mc-incorrect-answer2-${questionCounter}" name="mc_incorrect_answer2_${questionCounter}" placeholder="Enter incorrect answer 2"></textarea><br>

            <label for="mc-incorrect-answer3-${questionCounter}">Incorrect Answer 3:</label>
            <textarea id="mc-incorrect-answer3-${questionCounter}" name="mc_incorrect_answer3_${questionCounter}" placeholder="Enter incorrect answer 3"></textarea><br>
            
            <label for="mc-explanation-${questionCounter}">Explanation:</label>
            <textarea id="mc-explanation-${questionCounter}" name="mc_explanation_${questionCounter}" placeholder="Enter the explanation (optional)"></textarea><br><br>
            
            <button type="button" class="delete-question">Delete Question</button><br><br>
            `;
        container.appendChild(mcQuestionDiv);
        questionCounter++;
    }

    // Function to add text question block
    function addTextQuestion() {
        var container = document.getElementById('questions-container');
        var textQuestionDiv = document.createElement('div');
        textQuestionDiv.innerHTML = `
            <label for="text-question-${questionCounter}"><strong>Question ${questionCounter}: </strong></label>
            <textarea id="text-question-${questionCounter}" name="text_question_${questionCounter}" placeholder="Enter the question"></textarea><br><br>

            <label for="text-answer-${questionCounter}">Text Answer:</label>
            <textarea id="text-answer-${questionCounter}" name="text_answer_${questionCounter}" placeholder="Enter the answer"></textarea><br>
            
            <label for="text-explanation-${questionCounter}">Explanation:</label>
            <textarea id="text-explanation-${questionCounter}" name="text_explanation_${questionCounter}" placeholder="Enter the explanation (optional)"></textarea><br><br>
            
            <button type="button" class="delete-question">Delete Question</button><br><br>
            `;
        container.appendChild(textQuestionDiv);
        questionCounter++;
    }

    // Set questionCounter based on the number of existing questions
    var existingQuestions = document.querySelectorAll('.question-block').length;
    var questionCounter = existingQuestions + 1;

    // Add event listeners to buttons
    if (mcButton) {
        mcButton.addEventListener('click', addMultipleChoiceQuestion);
    }
    if (textButton) {
        textButton.addEventListener('click', addTextQuestion);
    }

    // Add event listener to form submit
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission
            var formData = new FormData(form);
            var actionUrl = form.action; // Use the action from the form

            fetch(actionUrl, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/assessment_centre'; // Redirect on success
                } else {
                    alert('Error updating the form: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error submitting the form');
            });
        });
    }
});

//David's satisfaction system
function submitTeacher() {
    var teacher = document.getElementById('teacherSelect').value;
    if (teacher) {
        sessionStorage.setItem('selectedTeacher', teacher);
        window.location.href = '/Satisfaction'; 
    } else {
        alert('Please select a teacher');
    }
}
//David's job end