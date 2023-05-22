package gpt

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"errors"
	"log"
)

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

func ExtractDWC(ocrText string) (map[string]interface{}, error) {
	promptSourceUrl := os.Getenv("GPT_PROMPT")
	presp, err := http.Get(promptSourceUrl)
	if err != nil {
		return nil, err
	}
	defer presp.Body.Close()

	if presp.StatusCode != http.StatusOK {
		return nil, errors.New(fmt.Sprintf("Error fetching the file, status code: %d", presp.StatusCode))
	}

	pbody, err := ioutil.ReadAll(presp.Body)
	if err != nil {
		return nil, err
	}

	systemPrompt := string(pbody)

	url := "https://api.openai.com/v1/chat/completions"
	log.Printf("Extracting DWC from: %s", ocrText)

	if ocrText == "" {
		return nil, errors.New("No text provided")
	}

	messages := []Message{
		{
			Role:    "system",
			Content: systemPrompt,
		},
		{
			Role:    "user",
			Content: ocrText,
		},
	}

	data := map[string]interface{}{
		"model":    os.Getenv("GPT_MODEL"),
		"messages": messages,
	}

	dataBytes, err := json.Marshal(data)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(dataBytes))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", os.Getenv("GPT_API_KEY")))

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var jsonResponse map[string]interface{}
	err = json.Unmarshal(body, &jsonResponse)
	if err != nil {
		return nil, err
	}

	log.Printf("Finished extracting DWC. Result: %s", jsonResponse)
	
	return jsonResponse, nil
}
