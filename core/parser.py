import ast


# ------------------------------------------------
# PARSE CODE FILES
# Python  -> AST based chunking
# Others  -> Line based chunking
# ------------------------------------------------

def parse_python_file(file_data):

    code = file_data["code"]

    file_path = file_data["file_path"]

    chunks = []
    chunk_idx = 0


    # ==============================
    # PYTHON AST CHUNKING
    # ==============================

    if file_path.endswith(".py"):

        try:

            tree = ast.parse(code)


            for node in ast.walk(tree):


                if isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.ClassDef
                    )
                ):


                    start_line = node.lineno


                    end_line = getattr(
                        node,
                        "end_lineno",
                        start_line
                    )


                    source = "\n".join(
                        code.splitlines()
                        [
                            start_line - 1:
                            end_line
                        ]
                    )


                    chunks.append(

                        {

                            "name": node.name,

                            "type": "python",

                            "file": file_path,

                            "start_line": start_line,

                            "end_line": end_line,

                            "code": source,

                            "chunk_index": chunk_idx

                        }

                    )
                    chunk_idx += 1


        except Exception:


            print(
                "Python parsing failed:",
                file_path
            )



    # ==============================
    # JS / JSX / TS / JAVA / CPP
    # NORMAL CHUNKING
    # ==============================

    else:


        lines = code.splitlines()


        chunk_size = 80


        for i in range(
            0,
            len(lines),
            chunk_size
        ):


            chunk_code = "\n".join(
                lines[
                    i:
                    i + chunk_size
                ]
            )


            if chunk_code.strip():


                chunks.append(

                    {

                        "name": "code_block",

                        "type": "general",

                        "file": file_path,

                        "start_line": i + 1,

                        "end_line": min(
                            i + chunk_size,
                            len(lines)
                        ),

                        "code": chunk_code,

                        "chunk_index": chunk_idx

                    }

                )
                chunk_idx += 1



    return chunks