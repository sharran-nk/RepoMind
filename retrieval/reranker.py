from sentence_transformers import CrossEncoder



class Reranker:


    def __init__(self):


        self.model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )



    def rerank(
        self,
        query,
        chunks,
        top_k=5
    ):


        pairs = []


        for chunk in chunks:


            pairs.append(

                [
                    query,
                    chunk["code"]
                ]

            )



        scores = self.model.predict(
            pairs
        )



        ranked = sorted(

            zip(
                scores,
                chunks
            ),


            key=lambda x:x[0],


            reverse=True

        )



        final = []


        for score,chunk in ranked[:top_k]:


            final.append(
                chunk
            )



        return final