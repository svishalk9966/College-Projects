// --- Globals & Elements ---
let quizData = [
  {
    question: "What is the capital of France?",
    options: ["Berlin", "London", "Paris", "Madrid"],
    correct: 2
  },
  {
    question: "Which planet is known as the Red Planet?",
    options: ["Earth", "Mars", "Jupiter", "Venus"],
    correct: 1
  },
  {
    question: "Who wrote 'Romeo and Juliet'?",
    options: ["Charles Dickens", "William Shakespeare", "Mark Twain", "Jane Austen"],
    correct: 1
  },
  {
    question: "What is 9 × 9?",
    options: ["81", "72", "99", "90"],
    correct: 0
  },
  {
    question: "What is the boiling point of water at sea level?",
    options: ["90°C", "100°C", "110°C", "120°C"],
    correct: 1
  },
  {
    question: "Which gas do plants absorb from the atmosphere?",
    options: ["Oxygen", "Nitrogen", "Carbon Dioxide", "Hydrogen"],
    correct: 2
  },
  {
    question: "What is the largest mammal in the world?",
    options: ["Elephant", "Blue Whale", "Giraffe", "Great White Shark"],
    correct: 1
  },
  {
    question: "Which language is primarily used for Android app development?",
    options: ["Swift", "Kotlin", "Ruby", "Python"],
    correct: 1
  },
  {
    question: "Who painted the Mona Lisa?",
    options: ["Vincent van Gogh", "Pablo Picasso", "Leonardo da Vinci", "Claude Monet"],
    correct: 2
  },
  {
    question: "What does HTTP stand for?",
    options: ["HyperText Transfer Protocol", "HighText Transfer Protocol", "HyperText Translate Protocol", "HyperText Transfer Program"],
    correct: 0
  },
  {
    question: "What is the largest continent by area?",
    options: ["Africa", "Asia", "Europe", "Antarctica"],
    correct: 1
  },
  {
    question: "Who discovered penicillin?",
    options: ["Alexander Fleming", "Marie Curie", "Isaac Newton", "Louis Pasteur"],
    correct: 0
  },
  {
    question: "What is the chemical symbol for gold?",
    options: ["Au", "Ag", "Fe", "Gd"],
    correct: 0
  },
  {
    question: "Which country hosted the 2016 Summer Olympics?",
    options: ["China", "Brazil", "UK", "Russia"],
    correct: 1
  },
  {
    question: "What is the formula for water?",
    options: ["H2O", "CO2", "O2", "HO"],
    correct: 0
  },
  {
    question: "Who is known as the Father of Computers?",
    options: ["Alan Turing", "Charles Babbage", "Bill Gates", "Steve Jobs"],
    correct: 1
  },
  {
    question: "What is the hardest natural substance on Earth?",
    options: ["Gold", "Iron", "Diamond", "Platinum"],
    correct: 2
  },
  {
    question: "In which year did World War II end?",
    options: ["1945", "1939", "1918", "1955"],
    correct: 0
  },
  {
    question: "Which organ in the human body pumps blood?",
    options: ["Lungs", "Kidney", "Heart", "Brain"],
    correct: 2
  },
  {
    question: "Which planet is closest to the Sun?",
    options: ["Venus", "Earth", "Mercury", "Mars"],
    correct: 2
  }
];

let currentQuestion = 0;
let score = 0;
let time = 15;
let timerInterval;
let autoNextTimeout;
let userAnswers = [];

const welcomeScreen = document.getElementById("welcome-screen");
const quizScreen = document.getElementById("quiz-screen");
const resultScreen = document.getElementById("result-screen");
const reviewScreen = document.getElementById("review-screen");

const questionText = document.getElementById("question-text");
const optionsContainer = document.getElementById("options");
const nextBtn = document.getElementById("next-btn");
const timeDisplay = document.getElementById("time");
const scoreDisplay = document.getElementById("score");

const startBtn = document.getElementById("start-btn");
const restartBtn = document.getElementById("restart-btn");
const reviewBtn = document.getElementById("review-btn");
const goHomeBtn = document.getElementById("go-home-btn");

const darkModeToggle = document.getElementById("dark-mode-toggle");
const bodyElement = document.getElementById("body");

const soundCorrect = document.getElementById("sound-correct");
const soundWrong = document.getElementById("sound-wrong");
const soundTimeup = document.getElementById("sound-timeup");

// --- Event Listeners ---
startBtn.addEventListener("click", startQuiz);
restartBtn.addEventListener("click", startQuiz);
reviewBtn.addEventListener("click", showReview);
goHomeBtn.addEventListener("click", goHome);
nextBtn.addEventListener("click", loadNextQuestion);
darkModeToggle.addEventListener("click", toggleDarkMode);

// --- Functions ---

function startQuiz() {
  currentQuestion = 0;
  score = 0;
  userAnswers = [];

  welcomeScreen.classList.add("d-none");
  reviewScreen.classList.add("d-none");
  resultScreen.classList.add("d-none");
  quizScreen.classList.remove("d-none");

  // Add gradient background when quiz starts
  bodyElement.classList.add("gradient-background");

  loadQuestion();
}

function loadQuestion() {
  resetState();
  clearTimeout(autoNextTimeout);

  const q = quizData[currentQuestion];
  questionText.textContent = `Q${currentQuestion + 1}. ${q.question}`;

  q.options.forEach((option, index) => {
    const btn = document.createElement("button");
    btn.textContent = option;
    btn.classList.add("btn", "btn-outline-primary");
    btn.addEventListener("click", () => selectAnswer(index, btn));
    optionsContainer.appendChild(btn);
  });

  startTimer();
}

function resetState() {
  clearInterval(timerInterval);
  clearTimeout(autoNextTimeout);
  time = 15;
  timeDisplay.textContent = time;
  nextBtn.disabled = true;
  optionsContainer.innerHTML = "";
}

function startTimer() {
  timerInterval = setInterval(() => {
    time--;
    timeDisplay.textContent = time;
    if (time <= 0) {
      clearInterval(timerInterval);
      if (soundTimeup) soundTimeup.play();

      disableOptionsWithoutHighlight();
      recordAnswer(null);

      nextBtn.disabled = false;

      autoNextTimeout = setTimeout(() => {
        loadNextQuestion();
      }, 2000);
    }
  }, 1000);
}

function disableOptionsWithoutHighlight() {
  Array.from(optionsContainer.children).forEach((btn) => {
    btn.disabled = true;
    btn.classList.remove("btn-outline-primary", "btn-success", "btn-danger");
  });
}

function selectAnswer(index, selectedBtn) {
  clearInterval(timerInterval);
  clearTimeout(autoNextTimeout);

  const correct = quizData[currentQuestion].correct;

  Array.from(optionsContainer.children).forEach((btn, i) => {
    btn.disabled = true;
    btn.classList.remove("btn-outline-primary");
    if (i === correct) {
      btn.classList.add("btn-success");
    } else if (btn === selectedBtn) {
      btn.classList.add("btn-danger");
    }
  });

  if (index === correct) {
    score++;
    if (soundCorrect) soundCorrect.play();
  } else {
    if (soundWrong) soundWrong.play();
  }

  recordAnswer(index);
  nextBtn.disabled = false;
}

function recordAnswer(index) {
  const q = quizData[currentQuestion];
  userAnswers.push({
    question: q.question,
    options: q.options,
    correct: q.correct,
    selected: index
  });
}

function loadNextQuestion() {
  currentQuestion++;
  if (currentQuestion < quizData.length) {
    loadQuestion();
  } else {
    showResults();
  }
}

function showResults() {
  quizScreen.classList.add("d-none");
  resultScreen.classList.remove("d-none");
  scoreDisplay.textContent = `${score} / ${quizData.length}`;
}

function showReview() {
  resultScreen.classList.add("d-none");
  reviewScreen.classList.remove("d-none");
  renderReview();
}

function renderReview() {
  const reviewList = document.getElementById("review-list");
  reviewList.innerHTML = "";

  userAnswers.forEach((ua, idx) => {
    const div = document.createElement("div");
    div.classList.add("mb-3", "border", "p-2", "rounded");

    const qEl = document.createElement("p");
    qEl.innerHTML = `<strong>Q${idx + 1}:</strong> ${ua.question}`;
    div.appendChild(qEl);

    ua.options.forEach((opt, i) => {
      const optBtn = document.createElement("button");
      optBtn.classList.add("btn", "btn-sm", "me-2", "mb-1");
      optBtn.disabled = true;

      if (ua.selected === null) {
        optBtn.classList.add("btn-outline-secondary");
      } else {
        if (i === ua.correct) {
          optBtn.classList.add("btn-success");
        } else if (i === ua.selected) {
          optBtn.classList.add("btn-danger");
        } else {
          optBtn.classList.add("btn-outline-secondary");
        }
      }
      optBtn.textContent = opt;
      div.appendChild(optBtn);
    });

    reviewList.appendChild(div);
  });
}

function goHome() {
  reviewScreen.classList.add("d-none");
  welcomeScreen.classList.remove("d-none");

  // Remove gradient background on going home
  bodyElement.classList.remove("gradient-background");
}

function toggleDarkMode() {
  bodyElement.classList.toggle("dark-mode");
  if (bodyElement.classList.contains("dark-mode")) {
    darkModeToggle.textContent = "Light Mode";
  } else {
    darkModeToggle.textContent = "Dark Mode";
  }
}
