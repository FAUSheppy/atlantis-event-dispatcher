FROM alpine

WORKDIR /app/
RUN apk --update --no-cache add python3 py3-requests

COPY ./*.py ./

ENTRYPOINT ["python"]
CMD ["dispatch-query.py"]
