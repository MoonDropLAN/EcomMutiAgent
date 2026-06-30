def compose_response(state: dict) -> dict:
    if state.get("final_answer"):
        return state
    if state.get("need_clarification"):
        missing = "、".join(state.get("missing_slots", [])) or "更多信息"
        state["final_answer"] = f"我还需要补充信息：{missing}。"
        return state
    products = state.get("recommended_products", [])
    coupon_plan = state.get("coupon_plan")
    snippets = state.get("knowledge_snippets", [])
    if products and coupon_plan:
        product_name = products[0]["name"]
        payable = coupon_plan["best_plan"]["payable_amount"]
        state["final_answer"] = f"推荐 {product_name}，优惠后预计支付 {payable} 元。"
    elif products:
        state["final_answer"] = f"推荐 {products[0]['name']}。"
    elif snippets:
        state["final_answer"] = snippets[0]["content"]
    elif state.get("intent") == "knowledge_qa":
        state["final_answer"] = "我没有检索到可靠政策内容，建议转人工确认。"
    else:
        state["final_answer"] = "我可以帮你进行商品导购、优惠计算或订单查询。"
    return state