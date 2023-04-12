package main

import (
	"encoding/json"
	gcv "gcv-ocr/api"
	"log"
	"os"

	"github.com/streadway/amqp"
)

// Configuration settings.
const ()

func main() {
	conn, err := amqp.Dial(os.Getenv("RABBIT_MQ_URI"))
	if err != nil {
		log.Fatalf("Failed to connect to RabbitMQ: %s", err)
	}
	defer conn.Close()

	ch, err := conn.Channel()
	if err != nil {
		log.Fatalf("Failed to open a channel: %s", err)
	}
	defer ch.Close()

	qIn, err := ch.QueueDeclare(
		os.Getenv("INPUT_QUEUE_GCV_OCR"),
		false,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Fatalf("Failed to declare a queue: %s", err)
	}

	qOut, err := ch.QueueDeclare(
		os.Getenv("INPUT_QUEUE_ANNOTATE"),
		false,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Fatalf("Failed to declare a queue: %s", err)
	}

	msgs, err := ch.Consume(
		qIn.Name,
		"",
		true,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Fatalf("Failed to register a consumer: %s", err)
	}

	forever := make(chan bool)

	type Message struct {
		ID   string `json:"id"`
		Text string `json:"text"`
		Source string `json:"Source"`
	}

	go func() {
		for d := range msgs {
			var msg Message
			if err := json.Unmarshal(d.Body, &msg); err != nil {
				log.Printf("Failed to decode message: %s", err)
				log.Printf("Failed to decode message: %s", d.Body)
				continue
			}
			
			response, err := gcv.SendToOCR(msg.Text)
			if err != nil {
				log.Printf("Error running sendToOCR: %s", err)
				continue
			} 

			responseBytes, err := json.Marshal(response.GetTextAnnotations())
			if err != nil {
				log.Fatalf("Error converting text annotations to JSON: %v", err)
			}

			newFullMsg := Message{
				ID:      msg.ID,
				Text:    string(responseBytes),
				Source:  "gcv_pages",
			}

			fullMsgBytes, err := json.Marshal(newFullMsg)
			if err != nil {
				log.Printf("Failed to encode message: %s", err)
				return
			}

			err = ch.Publish(
				"",
				qOut.Name,
				false,
				false,
				amqp.Publishing{
					ContentType: "application/json",
					Body:        fullMsgBytes,
				})
			if err != nil {
				log.Printf("Failed to publish a message: %s", err)
			}
		}
	}()

	log.Printf(" [*] Waiting for messages. To exit press CTRL+C")
	<-forever
}
