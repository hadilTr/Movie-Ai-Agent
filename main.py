from tools.graph_query_tool import query as graph_query
from tools.search_tool import vector_search
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from typing import TypedDict, Annotated, Sequence
from langchain_groq import ChatGroq
import operator
import os
from dotenv import load_dotenv

load_dotenv()


llm = ChatGroq(
    api_key=os.getenv("groq_api_key"),
    model="llama-3.3-70b-versatile",
    temperature=0
)


system_prompt = """You are a movie database assistant with access to a Neo4j graph database.

DATABASE SCHEMA:
- Nodes: movie (id, title, year, plot, plot_embedding), person (id, name, bio)
- Relationships: ACTED_IN, DIRECTED

TOOLS:
1. query: Execute Cypher queries for exact matches (titles, actors, directors, years)
2. vector_search: Semantic search using plot_embedding for themes/concepts

DECISION RULES:
- User asks for specific title/actor/director → Use query with Cypher
- User asks about themes/plot/concepts → Use vector_search
- "supernatural" as a title → Use query
- "supernatural movies" (theme) → Use vector_search

RESPONSE RULES:
1. Execute the tool immediately - no explanation beforehand
2. If query returns empty: State "No results found" - do NOT offer alternatives unprompted
3. Present results clearly in bullet points
4. Be concise - no verbose explanations
5. Format output as:
   - Movie: [title] ([year])
   - Director: [name]
   - Actors: [list]
   - Plot: [summary]


"""


tools = [graph_query, vector_search]
llm_with_tools = llm.bind_tools(tools)  


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


def agent_node(state: AgentState):
    messages = state["messages"]
    messages_with_system = [SystemMessage(content=system_prompt)] + messages
    response = llm_with_tools.invoke(messages_with_system)
    return {"messages": [response]}


tool_node = ToolNode(tools)


def should_continue(state: AgentState):
    last_msg = state["messages"][-1]
    return "tools" if getattr(last_msg, "tool_calls", None) else END

# the graph workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")
app = workflow.compile()




def run_query(query: str):
    """Run query and return final answer only"""
    initial_state = {"messages": [HumanMessage(content=query)]}
    final_state = app.invoke(initial_state, config={"recursion_limit": 20})  
    final_msg = final_state["messages"][-1]
    return getattr(final_msg, "content", None)


def run_query_with_tools(query: str):
    
    initial_state = {"messages": [HumanMessage(content=query)]}
    
    
    tools_used = []
    
    for output in app.stream(initial_state, config={"recursion_limit": 20}):
        for node_name, node_output in output.items():
            if "messages" in node_output:
                last_msg = node_output["messages"][-1]
                tool_calls = getattr(last_msg, "tool_calls", None)
                
                if tool_calls:
                  for tool_call in tool_calls:
                    match tool_call.get("name"):
                        case "query":
                            tools_used.append({
                                "tool_name": "graph_query",
                                "arguments": tool_call.get("args"),
                                "id": tool_call.get("id")
                            })
                        case "vector_search":
                            tools_used.append({
                                "tool_name": "vector_search",
                                "arguments": tool_call.get("args"),
                                "id": tool_call.get("id")
                })
                            
    final_state = app.invoke(initial_state)
    final_msg = final_state["messages"][-1]
    answer = getattr(final_msg, "content", None)
    
    return answer, tools_used



def run_query_debug(query: str):
    """Run query with debug output"""
    initial_state = {"messages": [HumanMessage(content=query)]}
    
    print("=== DEBUG MODE ===\n")
    for output in app.stream(initial_state):
        for node_name, node_output in output.items():
            if "messages" in node_output:
                last_msg = node_output["messages"][-1]
                content = getattr(last_msg, "content", None)
                tool_calls = getattr(last_msg, "tool_calls", None)
                
                print(f"--- Node: {node_name} ---")
                if content:
                    print(f"Content: {content[:200]}...")
                if tool_calls:
                    print(f"Tool Calls: {tool_calls}")
                print()
    
    # Return final result
    final_state = app.invoke(initial_state)
    final_msg = final_state["messages"][-1]
    return getattr(final_msg, "content", None)

if __name__ == "__main__":

    """Generate and save graph visualization"""
    # try:
    #     img = app.get_graph().draw_mermaid_png()
    #     with open("react_agent_graph.png", "wb") as f:
    #         f.write(img)
    # except Exception as e:
    #     print(f"Could not generate graph visualization: {e}")

    """Example query run and tool usage printout"""
    queries = ["List all movies directed by Christopher Nolan"," Give me a film about dream invasion"]
    for query in queries:
        answer, tools_used = run_query_with_tools(query)
        print("=== QUERY ===")
        print(f"Query: {query}\n")
        print(f"Answer: {answer}\n")
        print(f"Tools Used: {tools_used}\n")
    