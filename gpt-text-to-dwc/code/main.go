package main

import (
	"encoding/json"
	gpt "gpt-text-to-dwc/api"
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
		os.Getenv("INPUT_QUEUE_GPT"),
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
			
			response, err := gpt.ExtractDWC(msg.Text)
			if err != nil {
				log.Printf("Error running extractDWC: %s", err)
				continue
			} 

			responseBytes, err := json.Marshal(response)
			if err != nil {
				log.Printf("Failed to encode response: %s", err)
				continue
			}

			newMsg := Message{
				ID:      msg.ID,
				Text:    string(responseBytes),
				Source:  "gpt4",
			}

			msgBytes, err := json.Marshal(newMsg)
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
					Body:        msgBytes,
				})
			if err != nil {
				log.Printf("Failed to publish a message: %s", err)
			}
		}
	}()

	log.Printf(" [*] Waiting for messages. To exit press CTRL+C")
	<-forever
}
