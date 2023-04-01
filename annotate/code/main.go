package main

import (
	"encoding/json"
	annotate "annotate/api"
	"log"
	"os"
	"github.com/streadway/amqp"
)

// Configuration settings.
const ()

func main() {
	conn, err := amqp.Dial(os.Getenv("RABBIT_MQ_URI"))
	if err != nil { log.Fatalf("Failed to connect to RabbitMQ: %s", err) }
	defer conn.Close()

	ch, err := conn.Channel()
	if err != nil { log.Fatalf("Failed to open a channel: %s", err) }
	defer ch.Close()

	qInGPT, err := ch.QueueDeclare(os.Getenv("INPUT_QUEUE_ANNOTATE_GPT"), false, false, false, false, nil)
	if err != nil { log.Fatalf("Failed to declare a queue: %s", err) }

	qOut, err := ch.QueueDeclare(os.Getenv("OUTPUT_QUEUE_ANNOTATE"), false, false, false, false, nil)
	if err != nil { log.Fatalf("Failed to declare a queue: %s", err) }

	qInPythonDWC, err := ch.QueueDeclare(os.Getenv("OUTPUT_QUEUE_PYTHON_DWC"), false, false, false, false, nil)
	if err != nil { log.Fatalf("Failed to declare a queue: %s", err) }

	msgsGPT, err := ch.Consume(qInGPT.Name, "", true, false, false, false, nil)
	if err != nil { log.Fatalf("Failed to register a consumer: %s", err) }

	msgsPythonDWC, err := ch.Consume(qInPythonDWC.Name, "", true, false, false, false, nil)
	if err != nil { log.Fatalf("Failed to register a consumer: %s", err) }

	forever := make(chan bool)

	type Message struct {
		ID   string `json:"id"`
		Text string `json:"text"`
	}

	go processMessages(msgsGPT, ch, qOut, "gpt4")
	go processMessages(msgsPythonDWC, ch, qOut, "pythondwc_v1")

	log.Printf(" [*] Waiting for messages. To exit press CTRL+C")
	<-forever
}

func processMessages(msgs <-chan amqp.Delivery, ch *amqp.Channel, qOut amqp.Queue, modelName string) {
	type Message struct {
		ID   string `json:"id"`
		Text string `json:"text"`
	}

	for d := range msgs {
		var msg Message
		if err := json.Unmarshal(d.Body, &msg); err != nil {
			log.Printf("Failed to decode message: %s", err)
			continue
		}

		response, err := annotate.Annotate(&msg.ID, &msg.Text, modelName, "")
		if err != nil {
			log.Printf("Error running annotate: %s", err)
			continue
		}

		responseBytes, err := json.Marshal(response)
		if err != nil {
			log.Printf("Failed to encode response: %s", err)
			continue
		}

		err = ch.Publish(
			"",
			qOut.Name,
			false,
			false,
			amqp.Publishing{
				ContentType: "application/json",
				Body:        responseBytes,
			})
		if err != nil {
			log.Printf("Failed to publish a message: %s", err)
		}
	}
}
