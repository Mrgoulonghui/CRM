var pop_back_id;  // 定义一个全局的变量,记录要给那个标签 进行dom渲染操作
function pop(url, back_id) {
    pop_back_id = back_id;  // 把那个拼接的id值,赋给全局变量pop_back_id,做DOM操作使用
    window.open(url+"?pop=1", url+"?pop=1", "width=800, height=500, top=100, left=100")
    // 给url + "?pop=1",是加一个参数,与正常添加 作区分,,如果能取到pop参数,说明是pop窗口的添加,
    // 我们需要返回的就不是查看页面了,而是返回原来的页面,做dom操作
}

// pop窗口的操作完成之后,利用子窗口关闭之前,调用这个方法,进行父窗口的渲染
function pop_back_func(text, pk) {
    console.log(text, pk);
    console.log("--->", pop_back_id);

    var $option = $("<option>");  // jquery 创建一个<option></option>标签
    $option.text(text);
    $option.attr("value", pk);
    $option.attr("selected", "selected");  // 注意 这里两个都是字符串形式

    $("#"+pop_back_id).append($option);  // 把这个标签添加到我们的那个标记好的 select标签中

}