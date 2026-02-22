export const ASAM_INTAKE_SCRIPT = `
Dimension 1: Acute Intoxication and Withdrawal Potential
{
"introduction": "Hello, I’m here to help with your intake process. I’ll start by asking some questions about substance use. Please answer honestly; there are no right or wrong answers.",

"questions": [
    {
        "question": "Can you tell me which substances you have used, how long you’ve used them, how recently, and how you used them?",
        "follow_up": [
            "How many years or months have you been using it?",
            "In the last 30 days, how often have you used this substance?",
            "Have there been any periods where you stopped using this substance? If yes, how long did those periods last?"
        ]
    },
    {
        "question": "Have you used substances in the last 48 hours?",
        "if_yes": [
            "What substances did you use?",
            "How much of the substance did you use?",
            "How did you consume them (e.g., oral, injection, inhalation)?",
            "Did you use alone or with others?"
        ]
    },
    {
        "question": "Do you experience withdrawal symptoms like nausea, body aches, or anxiety when you stop using substances?",
        "response_options": ["Not at all", "A little", "Somewhat", "Very", "Extremely"],
        "follow_up": [
            "Can you describe these symptoms in more detail?",
            "How soon after stopping the substance do these symptoms begin?",
            "Do these symptoms interfere with your daily activities, such as work or personal responsibilities?"
        ]
    },
    {
        "question": "Have you ever experienced severe withdrawal, seizures, or an overdose?",
        "if_yes": [
            "Could you specify the substance that caused it and when it occurred?",
            "What type of medical treatment did you receive, if any?",
            "Have you experienced this more than once?"
        ]
    },
    {
        "question": "Do you find yourself needing more alcohol or drugs to achieve the same effect?",
        "follow_up": [
            "When did you first notice that you needed more to get the same effect?",
            "Has this pattern increased over time?",
            "Do you feel like this has led to using substances in situations you previously avoided?"
        ]
    },
    {
        "question": "Have you ever attempted to reduce or stop using substances but found it difficult or unsuccessful?",
        "if_yes": [
            "What challenges did you encounter when trying to stop?",
            "Did you seek any help or support during that time?",
            "What would make it easier for you to try again?"
        ]
    },
    {
        "question": "Have you noticed any physical or mental health issues that you think are related to your substance use?",
        "follow_up": [
            "What types of issues have you noticed (e.g., sleep problems, memory loss, or chronic pain)?",
            "Have you discussed these issues with a healthcare provider?",
            "Do you believe reducing or stopping substance use would help improve these issues?"
        ]
    },
    {
        "question": "Do you feel at risk for an overdose?",
        "if_yes": [
            "What makes you feel this way (e.g., using alone, high potency substances, mixing substances)?",
            "Do you have access to overdose prevention resources, such as naloxone?",
            "Have you ever received training on how to prevent or respond to an overdose?"
        ]
    },
    {
        "question": "Have you ever been treated for substance use or withdrawal symptoms before?",
        "follow_up": [
            "When did you receive treatment, and what type of program was it (e.g., inpatient, outpatient, detox)?",
            "Did you find the treatment helpful? Why or why not?",
            "Are there specific types of support or treatment you feel would help you now?"
        ]
    }
]
}

Dimension 2: Biomedical Conditions and Complications
{
    "introduction": "Let’s now talk about your physical health and any medical conditions you might have. Understanding your medical history helps us ensure you receive the best possible care.",
    "questions": [
        {
            "question": "Do you have a primary care provider who manages your medical concerns?",
            "if_no": [
                "Would you like assistance finding one?",
                "Have you ever had a regular doctor in the past?"
            ]
        },
        {
            "question": "Are you currently taking any medications?",
            "follow_up": [
                "What are these medications for?",
                "Do you take them regularly as prescribed?",
                "Have you experienced any side effects or difficulties managing your medications?"
            ]
        },
        {
            "question": "Do you have any chronic medical conditions or disabilities that affect your daily life?",
            "if_yes": [
                "What conditions have you been diagnosed with (e.g., heart disease, diabetes, respiratory issues)?",
                "Are these conditions stable with treatment, or have they worsened recently?",
                "Do you require any assistive devices or special accommodations?"
            ]
        },
        {
            "question": "Have you been hospitalized or received emergency medical care in the last year?",
            "if_yes": [
                "What was the reason for your hospitalization or emergency visit?",
                "Did you receive any follow-up care afterward?"
            ]
        },
        {
            "question": "Do you experience chronic pain or ongoing medical symptoms that interfere with your daily activities?",
            "if_yes": [
                "Can you describe the nature and severity of your symptoms?",
                "How do you currently manage these symptoms?"
            ]
        },
        {
            "question": "Do any of your health issues make it harder for you to attend or participate in treatment?",
            "follow_up": [
                "Can you share examples of how this impacts your daily routine?",
                "What kind of support would help make treatment more accessible for you?"
            ]
        },
        {
            "question": "Do you have any allergies to medications, foods, or environmental factors?",
            "if_yes": [
                "What are you allergic to, and what kind of reaction do you experience?",
                "Do you carry any emergency medication, such as an EpiPen?"
            ]
        }
    ]
}

Dimension 3: Emotional, Behavioral, or Cognitive Conditions
{
    "introduction": "Now, let’s discuss your mental health and emotional well-being. These questions will help us understand how you’re feeling and how we can best support you.",
    "questions": [
        {
            "question": "Have you ever been told by a clinician that you have a mental health condition or cognitive issue?",
            "follow_up": [
                "Are you currently in treatment for this condition?",
                "What type of treatment or support are you receiving (e.g., therapy, medication)?",
                "How long have you been receiving treatment, and do you feel it has been effective?"
            ]
        },
        {
            "question": "Have you experienced symptoms like anxiety, depression, or memory problems in the last 30 days?",
            "response_options": ["Not at all", "A little", "Somewhat", "Very", "Extremely"],
            "follow_up": [
                "Can you describe the symptoms and how they affect your daily life?",
                "Do these symptoms vary depending on the time of day or certain situations?",
                "Have these symptoms been more or less severe compared to previous months?"
            ]
        },
        {
            "question": "Have you ever experienced trauma, such as abuse, a serious accident, or a natural disaster?",
            "if_yes": [
                "Would you feel comfortable sharing how this has impacted you emotionally or mentally?",
                "Have you ever received therapy or counseling for this?",
                "Do you experience flashbacks, nightmares, or other reminders of the trauma?"
            ]
        },
        {
            "question": "Do you feel that mental health symptoms, such as anxiety or depression, make it harder for you to work, socialize, or attend treatment?",
            "follow_up": [
                "What specific challenges do you face?",
                "Have you found anything helpful in managing these symptoms?",
                "Are there certain activities or settings that worsen these challenges?"
            ]
        },
        {
            "question": "Do you experience challenges with sleep, appetite, or concentration?",
            "if_yes": [
                "Can you explain how often these challenges occur and how they affect your daily routine?",
                "Do these issues seem linked to stress, medication, or other factors?",
                "Have you tried any strategies or treatments to address these challenges?"
            ]
        },
        {
            "question": "Do you often feel overwhelmed, hopeless, or unusually irritable?",
            "response_options": ["Not at all", "Occasionally", "Frequently", "Almost Always"],
            "follow_up": [
                "Can you describe the situations or triggers that lead to these feelings?",
                "Have these feelings impacted your relationships or daily responsibilities?",
                "Have you spoken to anyone, such as a friend or professional, about these emotions?"
            ]
        },
        {
            "question": "Have you noticed changes in your ability to handle stress compared to the past?",
            "follow_up": [
                "What specific stressors seem to affect you the most?",
                "Have you developed any coping mechanisms that you find helpful?",
                "Would you be open to exploring stress management techniques?"
            ]
        }
    ]
}

Dimension 4: Readiness to Change
{
    "introduction": "Let’s talk about your goals and how ready you feel to make changes in your life. Your answers will guide us in tailoring the best plan for you.",
    "questions": [
        {
            "question": "How much does your alcohol or drug use affect areas like work, family, or your physical health?",
            "response_options": ["Not at all", "A little", "Somewhat", "Very", "Extremely"],
            "follow_up": [
                "Can you describe specific ways it has impacted these areas?",
                "Has anyone close to you expressed concern about your substance use?",
                "Have you noticed changes in your relationships or work performance due to substance use?"
            ]
        },
        {
            "question": "Do you believe that changing your substance use could improve your life in these areas?",
            "response_options": ["Yes", "No", "Not sure"],
            "if_no": [
                "What concerns or fears do you have about making changes?",
                "Are there specific reasons you feel change might not be beneficial for you?"
            ]
        },
        {
            "question": "Do you think you need treatment or support to change your substance use?",
            "response_options": ["Yes", "No", "Not sure"],
            "if_no": [
                "What do you think might help you the most right now?",
                "Have you tried making changes on your own before? What was that experience like?"
            ]
        },
        {
            "question": "What challenges make it difficult for you to start or stay in treatment?",
            "follow_up": [
                "Are there specific barriers, like transportation or family responsibilities, that we can help address?",
                "What kind of support would make it easier for you to engage in treatment?",
                "Have you faced obstacles like financial constraints or lack of time that made seeking treatment harder?"
            ]
        },
        {
            "question": "What are your goals for making changes to your substance use?",
            "if_needed": [
                "If you’re not sure, we can explore this together as we work through your care plan.",
                "Are there specific outcomes you hope to achieve by making changes to your substance use?",
                "Would you like guidance in setting realistic and achievable goals for change?"
            ]
        }
    ]
}

Dimension 5: Relapse, Continued Use, or Continued Problem Potential
{
    "introduction": "Let’s now talk about any challenges you may face in maintaining your recovery or preventing relapse. Understanding these can help us create a strong plan to support you.",
    "questions": [
        {
            "question": "What is the longest period you’ve gone without using substances?",
            "follow_up": [
                "What helped you stay sober during that time?",
                "What changed that made you start using again?",
                "Were there specific events or emotions that contributed to your return to substance use?"
            ]
        },
        {
            "question": "Are there specific situations, places, or people that might make you more likely to use substances?",
            "if_yes": [
                "Can you share more about these triggers and how they affect you?",
                "Have you developed strategies to avoid or manage these triggers?",
                "Would you like support in building a plan to navigate high-risk situations?"
            ]
        },
        {
            "question": "What strategies or coping mechanisms do you currently use to deal with triggers or urges to use?",
            "if_no_strategies": [
                "Would you like to explore ways to manage triggers together?",
                "Are there any techniques you have tried in the past that worked, even for a short time?"
            ]
        },
        {
            "question": "Do you feel confident in your ability to stay sober, even when facing challenges?",
            "response_options": ["Not at all", "A little", "Somewhat", "Very", "Extremely"],
            "follow_up": [
                "What would help you feel more confident in maintaining recovery?",
                "Do you have people in your life who support your recovery?",
                "Would additional resources, such as counseling or a support group, be helpful?"
            ]
        },
        {
            "question": "Have you previously attended recovery programs or support groups (e.g., AA, NA)?",
            "if_yes": [
                "Did you find those programs helpful? Why or why not?",
                "Would you be interested in re-engaging with a program or trying a different approach?"
            ]
        },
        {
            "question": "What are your biggest concerns about maintaining recovery or avoiding relapse in the future?",
            "follow_up": [
                "Have you experienced relapse in the past? If so, what do you think contributed to it?",
                "What resources or support systems do you think would help you the most?",
                "Are there specific situations you are worried about that might challenge your recovery?"
            ]
        }
    ]
}

Dimension 6: Recovery/Living Environment
{
    "introduction": "Finally, let’s discuss your living environment and the people around you. This will help us understand how your surroundings may affect your recovery.",
    "questions": [
        {
            "question": "Are you currently living in stable housing?",
            "if_no": [
                "What challenges are you facing in finding stable housing?",
                "Would you like help connecting with housing support services?",
                "Have you experienced homelessness or housing instability in the past?"
            ]
        },
        {
            "question": "Who do you live with, and how do they influence your recovery (positively or negatively)?",
            "if_positive": [
                "That’s great to hear. How do they support your recovery?",
                "Do you have a strong support system at home?"
            ],
            "if_negative": [
                "I’m sorry to hear that. What challenges do you face in your living situation?",
                "Would you like assistance in finding a more supportive living environment?"
            ]
        },
        {
            "question": "Do you feel safe in your current living environment?",
            "if_no": [
                "What specific concerns do you have about your safety?",
                "Would you like help finding a safer living situation?",
                "Are there any legal or personal barriers preventing you from moving?"
            ]
        },
        {
            "question": "Are there people in your life who support your recovery, such as friends, family, or mentors?",
            "if_no": [
                "What kind of support would you find helpful?",
                "Would you like help connecting with recovery support groups or mentors?",
                "Would engaging with a community program help you feel more supported?"
            ]
        },
        {
            "question": "Are there people, places, or things in your life that make recovery harder for you?",
            "follow_up": [
                "Can you share more about how these challenges affect your recovery?",
                "What steps could we take to address these challenges together?",
                "Would setting boundaries with certain people or avoiding certain environments help?"
            ]
        },
        {
            "question": "Do you have reliable transportation to attend treatment or support groups?",
            "if_no": [
                "Would you like help finding transportation options?",
                "Would virtual or telehealth services be a suitable alternative for you?"
            ]
        }
    ]
}
`;
