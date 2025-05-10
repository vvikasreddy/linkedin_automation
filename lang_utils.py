from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
from langchain_core.tools import tool

@tool(description="Calculate similarity score between two sentences using a language model.")
def text_similarity(sentence1: str, sentence2: str) -> bool:
    
    llm = ChatOllama(
        model="phi3:3.8b",
        temperature=0.0,
        return_messages=True,
        verbose=True,
    )

    prompt = ChatPromptTemplate.from_messages(
    [(
        "system",
        """You are a precise assistant who evaluates the semantic similarity between two sentences.
        1. {sentence1}
        2. {sentence2} and 
        amd only responds with either 'yes' or 'no', nothing else."""
    ),
    ("human", "{input}")
    ])

    chain = RunnableParallel(
        input=RunnablePassthrough(),
        sentence1 = RunnablePassthrough(),
        sentence2 = RunnablePassthrough()
    )| prompt | llm | RunnableLambda(
        lambda x: x.content.split("input")[0].strip().lower()) # get the first message content

    response = chain.invoke(
        {
        "input":"Am I on the messaging overlay? Respond with only 'yes' or 'no'",
        "sentence1":sentence1,
        "sentence2":sentence2
        })

    # print(response)
    return True if "yes" in response else False

# assert text_similarity.invoke({"sentence1" :"You are on the messaging overlay. Press enter to open the list of conversations.", 
#     "sentence2" : "conversations list opened"}) == False

# text_similarity.invoke({"sentence1" :"You are on the messaging overlay. Press enter to open the list of conversations.", 
#     "sentence2" : "conversations list opened"})